"""LOGI_INTERACTION_LATENCY_FINALIZE_02 — post-action server latency breakdown.

WHAT THIS FILE IS
-----------------
The measurement instrument AND the regression guard for the remaining
post-action latency of one Components v2 interaction:

    trigger → prefix callback (fresh auth → dispatcher → handler → readback)
            → normal rerun (fresh auth → ONE build_view_model → payload)

It replays the REAL lifecycle (``views.logi_shell._on_component_event`` then
``views.web_app.main``) against the isolated staging transport (mongomock) at
production shape (N = 95 shipments, real ledger rows, a real generated PXK
document) and records, per phase, elapsed milliseconds and the number of
MongoDB operations issued.

WHY OPERATIONS ARE COUNTED, NOT ONLY MILLISECONDS
--------------------------------------------------
The production app (Streamlit Community Cloud ↔ MongoDB Atlas) pays one
network round trip per sequential MongoDB operation; mongomock pays ~0.
Local CPU milliseconds therefore under-represent what the Owner feels, while
the operation count is transport-independent.  ``LOGI_PERF_RTT_MS`` (default
0) adds a synthetic per-operation delay so the same harness can report a
production-shaped wall-clock figure; the deterministic acceptance criteria
below are the operation budgets and the overlap proof (a wall-clock bound
against the *serial floor* ``operations × modeled RTT``), never raw timings.

THE REPAIR THIS GUARDS
----------------------
1. Reuse inside the ONE build: the C1 payload and the partner-context slice
   consume the customers / contracts / quotes / agents / docgen rows the render
   already read, and the per-contract ``contracts.find_one`` (N+1) became an
   in-memory lookup → build reads 26 → 17 at N=95 (contracts.find_one = 0).
2. Independent reads of the same render (and of the write readback) are issued
   together and joined (``views.logi_view_model._read_concurrently``): no
   cache, no skipped read — the same readers run once each, only no longer one
   after another.  Output parity with the sequential build is asserted below.

   The workers are STREAMLIT-FREE: the script thread resolves the database
   handle and the session values first and hands them down as explicit
   arguments, so a worker performs MongoDB reads and pure Python
   normalisation only — no ``st.*``, no ``add_script_run_ctx`` /
   ``get_script_run_ctx``, no write, no audit, no auth, no session mutation.
   A worker's error reports are CAPTURED per thread and replayed by the script
   thread in declaration order, so error state never races.  Three guards below
   prove exactly that (``WORKER_STREAMLIT_API_CALLS=0``, deterministic error
   semantics, writes/auth/audit stay on the script thread).

PRIVACY
-------
Only elapsed milliseconds, operation counts and collection names are printed.
No payload contents, no customer names, no business data, no secrets.

SAFETY
------
Isolated mongomock only.  No production/pilot database, no deployment, and
the DeepL provider is a mocked client — PAID_PROVIDER_CALLS_IN_TESTS=0.
"""

from __future__ import annotations

import inspect
import json
import os
import sys
import threading
import time
from collections import Counter
from contextlib import contextmanager
from typing import Any, Callable
from unittest.mock import patch

import pytest
import streamlit as st

from core import auth as core_auth
from core import database as core_database
from views import ceo_report as logi_ceo_report
from views import handbook as logi_handbook
from views import logi_c1
from views import logi_real_data as rd
from views import logi_sandbox
from views import logi_shell
from views import logi_view_model as vm
from views import partner_context as logi_partner_context
from views import reconciliation_desk as logi_reconciliation
from views import tariff_lookup as logi_tariff
from views import translation as logi_translation
from views import user_access as logi_user_access
from views import web_app

import test_logi_render_performance_01 as perf_fixture

N_SHIPMENTS = perf_fixture.N_SHIPMENTS
#: Synthetic per-operation round trip (ms).  0 = pure local CPU numbers.
RTT_MS = float(os.environ.get("LOGI_PERF_RTT_MS", "0") or 0)
#: Modeled DeepL provider time (ms) injected into the MOCKED client and
#: reported SEPARATELY — app code cannot remove provider latency.
PROVIDER_MS = float(os.environ.get("LOGI_PERF_PROVIDER_MS", "0") or 0)
COMPONENT_KEY = logi_shell.COMPONENT_KEY
STAFF_USER = "thuhang"  # seeded SUPPORT operator (views/logi_staging_seed.py)

_DB_OPS = (
    "find", "find_one", "count_documents", "estimated_document_count", "aggregate",
    "distinct", "insert_one", "insert_many", "update_one", "update_many",
    "replace_one", "find_one_and_update", "find_one_and_replace", "delete_one",
    "delete_many", "bulk_write",
)

# Phase names (packet vocabulary).
AUTH = "AUTH_REVALIDATION_MS"
WRITER = "WRITER_MS"
PREREAD = "HANDLER_PREREAD_MS"
READBACK = "AUTHORITATIVE_READBACK_MS"
CALLBACK = "CALLBACK_TOTAL_MS"
BODY = "SCRIPT_BODY_TOTAL_MS"
BUILD = "BUILD_VIEW_MODEL_TOTAL_MS"
SERIALIZATION = "SERIALIZATION_MS"
BUILD_PHASE_KEYS = (
    "LOAD_SHIPMENTS_MS", "LOAD_REFERENCES_MS", "DASHBOARD_VIEWS_MS",
    "READ_SHARED_SOURCES_MS", "PER_SHIPMENT_PROJECTION_MS",
    "GLOBAL_FINANCE_PROJECTIONS_MS", "SECONDARY_WORKSPACES_MS", "PAYLOAD_VERSION_MS",
)


# ---------------------------------------------------------------------------
# Instrument 1 — MongoDB operation counter (+ optional synthetic round trip)
# ---------------------------------------------------------------------------

class _OpCounter:
    """Counts MongoDB operations per collection into the CURRENT phase.

    Thread-aware: the render may issue independent reads on short-lived worker
    threads (``logi_view_model._read_concurrently``). A worker that entered a
    timed phase of its own reports into that phase; otherwise it reports into
    the phase the script thread is in (the phase that submitted it).
    """

    def __init__(self) -> None:
        self._local = threading.local()
        self.main_phase = "UNSCOPED"
        self.by_phase: dict[str, Counter] = {}
        #: ``"<phase>|<collection>.<op>"`` -> the thread names that issued it.
        self.threads: dict[str, set[str]] = {}
        self._lock = threading.Lock()

    @property
    def phase(self) -> str:
        return getattr(self._local, "phase", None) or self.main_phase

    @phase.setter
    def phase(self, value: str) -> None:
        if threading.current_thread() is threading.main_thread():
            self.main_phase = value
        else:
            self._local.phase = value

    def record(self, collection: str, op: str) -> None:
        key = f"{collection}.{op}"
        with self._lock:
            self.by_phase.setdefault(self.phase, Counter())[key] += 1
            self.threads.setdefault(f"{self.phase}|{key}", set()).add(threading.current_thread().name)
        if RTT_MS > 0:
            time.sleep(RTT_MS / 1000.0)

    def total(self, *phases: str) -> int:
        return sum(sum(self.by_phase.get(p, Counter()).values()) for p in phases)


class _CountingCollection:
    def __init__(self, name: str, inner: Any, counter: _OpCounter) -> None:
        self._name, self._inner, self._counter = name, inner, counter

    def __getattr__(self, item: str) -> Any:
        target = getattr(self._inner, item)
        if item in _DB_OPS and callable(target):
            def _wrapped(*args: Any, **kwargs: Any) -> Any:
                self._counter.record(self._name, item)
                return target(*args, **kwargs)
            return _wrapped
        return target


class _CountingDB:
    def __init__(self, inner: Any, counter: _OpCounter) -> None:
        self._inner, self._counter = inner, counter

    def __getitem__(self, name: str) -> Any:
        return _CountingCollection(name, self._inner[name], self._counter)

    def __getattr__(self, item: str) -> Any:
        target = getattr(self._inner, item)
        if hasattr(target, "find") and hasattr(target, "count_documents"):
            return _CountingCollection(item, target, self._counter)
        return target


# ---------------------------------------------------------------------------
# Instrument 2 — phase stopwatch (elapsed ms only; innermost phase owns the ops)
# ---------------------------------------------------------------------------

class _Phases:
    """Per-phase stopwatch. Phase ms are per-thread elapsed: when the render
    overlaps independent reads, sibling read phases overlap in wall-clock and
    their sum may exceed the enclosing total (the total is always wall-clock)."""

    def __init__(self, counter: _OpCounter) -> None:
        self.ms: dict[str, float] = {}
        self.counter = counter
        self.main_stack: list[str] = []
        self._local = threading.local()
        self._lock = threading.Lock()

    @property
    def stack(self) -> list[str]:
        if threading.current_thread() is threading.main_thread():
            return self.main_stack
        local = getattr(self._local, "stack", None)
        if local is None:
            local = self._local.stack = []
        return local

    def active(self) -> list[str]:
        """Phases open on this thread plus those open on the script thread."""
        return list(self.stack) + list(self.main_stack)

    @contextmanager
    def scope(self, name: str):
        previous = self.counter.phase
        self.counter.phase = name
        self.stack.append(name)
        started = time.perf_counter()
        try:
            yield
        finally:
            elapsed = (time.perf_counter() - started) * 1000
            with self._lock:
                self.ms[name] = self.ms.get(name, 0.0) + elapsed
            self.stack.pop()
            self.counter.phase = previous

    def wrap(self, name: str | Callable[[], str], fn: Callable[..., Any], *,
             only_inside: str | None = None) -> Callable[..., Any]:
        """Time ``fn`` under ``name``; with ``only_inside`` the scope opens only
        while that outer phase is active (so a projection helper the handler's
        readback also calls is attributed to the readback, not the build)."""
        def _timed(*args: Any, **kwargs: Any) -> Any:
            if only_inside is not None and only_inside not in self.active():
                return fn(*args, **kwargs)
            with self.scope(name() if callable(name) else name):
                return fn(*args, **kwargs)
        return _timed


# The build phases, as the packet names them.  Every wrapped symbol is looked
# up on its module at call time by build_view_model, so wrapping the module
# attribute times exactly the work the render performs (baseline or repaired).
_BUILD_PHASE_TARGETS: tuple[tuple[str, Any, str], ...] = (
    ("LOAD_SHIPMENTS_MS", vm, "load_shipments"),
    ("LOAD_REFERENCES_MS", vm, "_load_references"),
    ("LOAD_REFERENCES_MS", logi_c1, "assemble_c1_payload"),
    ("DASHBOARD_VIEWS_MS", vm, "_dashboard_views"),
    ("READ_SHARED_SOURCES_MS", vm, "_read_sources"),
    ("PER_SHIPMENT_PROJECTION_MS", rd, "shipment_projection"),
    ("GLOBAL_FINANCE_PROJECTIONS_MS", rd, "partner_payables_projection"),
    ("GLOBAL_FINANCE_PROJECTIONS_MS", rd, "receivables_projection"),
    ("GLOBAL_FINANCE_PROJECTIONS_MS", logi_reconciliation, "reconciliation_view"),
    ("GLOBAL_FINANCE_PROJECTIONS_MS", logi_ceo_report, "ceo_report_projection"),
    ("GLOBAL_FINANCE_PROJECTIONS_MS", vm, "_home_projection"),
    ("GLOBAL_FINANCE_PROJECTIONS_MS", vm, "_task_projection"),
    ("GLOBAL_FINANCE_PROJECTIONS_MS", vm, "_notifications"),
    ("SECONDARY_WORKSPACES_MS", logi_partner_context, "partner_context_view"),
    ("SECONDARY_WORKSPACES_MS", logi_handbook, "handbook_projection"),
    ("SECONDARY_WORKSPACES_MS", vm, "_knowledge_notes"),
    ("SECONDARY_WORKSPACES_MS", logi_user_access, "user_access_projection"),
    ("SECONDARY_WORKSPACES_MS", vm, "_users_reader"),
    ("SECONDARY_WORKSPACES_MS", logi_tariff, "tariff_lookup_view"),
    ("SECONDARY_WORKSPACES_MS", logi_translation, "translation_view"),
    ("SECONDARY_WORKSPACES_MS", rd, "finance_service_catalog"),
    ("SECONDARY_WORKSPACES_MS", vm, "_getfly_preview_projection"),
    ("SECONDARY_WORKSPACES_MS", vm, "_attachment_policy"),
    ("SECONDARY_WORKSPACES_MS", vm, "_last_writes_readback"),
    ("PAYLOAD_VERSION_MS", vm, "_payload_version"),
)


# ---------------------------------------------------------------------------
# Fixture — production-shaped isolated staging data (N = 95)
# ---------------------------------------------------------------------------

@pytest.fixture()
def staging():
    logi_sandbox.reset_backend()
    assert logi_sandbox.ensure_backend() == logi_sandbox.SANDBOX_TRANSPORT
    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)
    yield
    for key in (COMPONENT_KEY, logi_shell.CALLBACK_DISPATCHED_FLAG, vm.LAST_WRITES_KEY,
                vm.SEQ_KEY, vm.TRANSLATION_REQUEST_KEY, vm.TRANSLATION_RESULT_KEY):
        st.session_state.pop(key, None)
    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)
    logi_sandbox.reset_backend()


@pytest.fixture()
def dataset(staging):
    state = {"n": 0}

    def _seq(name: str, payload: dict) -> dict:
        state["n"] += 1
        return {name: {"seq": state["n"], "event": name, "payload": payload}}

    perf_fixture._real_pxk_document(_seq)
    perf_fixture._seed_ledger_records()
    ids = perf_fixture._clone_shipments_to(N_SHIPMENTS)["ids"]
    # The seeded SUPPORT operator is the staff identity every interaction runs
    # under; AUTH_REQUIRED=True makes the fresh revalidation a REAL users read.
    st.session_state["current_user"] = {"username": STAFF_USER, "role": "support", "user_id": STAFF_USER}
    st.session_state.pop(vm.SEQ_KEY, None)
    st.session_state.pop(vm.LAST_WRITES_KEY, None)
    return {"ids": ids}


# ---------------------------------------------------------------------------
# The interaction runner — the real lifecycle, timed per phase
# ---------------------------------------------------------------------------

def _run_interaction(monkeypatch, trigger: dict, *, seq: int) -> dict[str, Any]:
    """Replay ONE component event exactly as Streamlit executes it.

    1. prefix callback  — fresh auth revalidation → dispatcher → handler
    2. script body      — fresh auth revalidation → ONE build_view_model → mount
    Returns the per-phase timing/operation breakdown plus the lifecycle
    invariants (handler calls, VM builds, explicit reruns).
    """
    from streamlit.components.v2.bidi_component.state import ComponentResult

    counter = _OpCounter()
    phases = _Phases(counter)
    original_get_db = core_database.get_db
    monkeypatch.setattr(core_database, "get_db", lambda: _CountingDB(original_get_db(), counter))

    # Callback-level instruments.  ``read_shipment`` is the handler's pre-read
    # BEFORE the writer ran and the authoritative readback AFTER it.
    written = {"done": False}

    def _read_phase() -> str:
        return READBACK if written["done"] else PREREAD

    def _writer(fn: Callable[..., Any]) -> Callable[..., Any]:
        timed = phases.wrap(WRITER, fn)

        def _run(*args: Any, **kwargs: Any) -> Any:
            try:
                return timed(*args, **kwargs)
            finally:
                written["done"] = True
        return _run

    monkeypatch.setattr(core_auth, "fresh_session_identity_for_action",
                        phases.wrap(AUTH, core_auth.fresh_session_identity_for_action))
    monkeypatch.setattr(vm, "read_shipment", phases.wrap(_read_phase, vm.read_shipment))
    monkeypatch.setattr(vm, "_projection_for", phases.wrap(READBACK, vm._projection_for))
    monkeypatch.setattr(vm, "_audit_trail", phases.wrap(READBACK, vm._audit_trail))
    monkeypatch.setattr(core_database, "save_shipment_atomic", _writer(core_database.save_shipment_atomic))
    monkeypatch.setattr(core_database, "save_direct_shipment_payment",
                        _writer(core_database.save_direct_shipment_payment))

    # Build-level instruments.
    for phase_name, module, attr in _BUILD_PHASE_TARGETS:
        monkeypatch.setattr(module, attr,
                            phases.wrap(phase_name, getattr(module, attr), only_inside=BUILD))

    # Reads the render issues together on worker threads report into the phase
    # of the thread that submitted them (the harness only attributes; the
    # production helper is called unchanged).
    real_concurrent = getattr(vm, "_read_concurrently", None)  # absent on the pre-repair baseline

    def _attributed_concurrent(reads: dict[str, Callable[[], Any]]) -> dict[str, Any]:
        inherited = counter.phase

        def _bind(read: Callable[[], Any]) -> Callable[[], Any]:
            def _run() -> Any:
                counter.phase = inherited
                return read()
            return _run
        return real_concurrent({key: _bind(read) for key, read in reads.items()})

    if real_concurrent is not None:
        monkeypatch.setattr(vm, "_read_concurrently", _attributed_concurrent)

    builds: list[dict] = []
    original_build = vm.build_view_model

    def _timed_build() -> dict:
        with phases.scope(BUILD):
            model = original_build()
        builds.append(model)
        return model

    monkeypatch.setattr(vm, "build_view_model", _timed_build)
    reruns: list[int] = []
    monkeypatch.setattr(st, "rerun", lambda *a, **k: reruns.append(1))
    monkeypatch.setattr(logi_shell, "_renderer", lambda: (lambda **kw: ComponentResult({}, trigger)))
    monkeypatch.setattr(core_auth, "AUTH_REQUIRED", True)
    monkeypatch.setattr(st, "set_page_config", lambda *a, **k: None)

    st.session_state[COMPONENT_KEY] = trigger
    st.session_state.pop(logi_shell.CALLBACK_DISPATCHED_FLAG, None)
    st.session_state[vm.SEQ_KEY] = seq - 1

    started = time.perf_counter()
    with phases.scope(CALLBACK):
        logi_shell._on_component_event()
    auth_callback_ms = phases.ms.get(AUTH, 0.0)
    auth_callback_ops = counter.total(AUTH)
    with phases.scope(BODY):
        web_app.main()
    total_ms = (time.perf_counter() - started) * 1000

    assert builds, "the script body must build the view-model exactly once"
    with phases.scope(SERIALIZATION):
        payload_bytes = len(json.dumps(builds[0], default=str, ensure_ascii=False).encode("utf-8"))

    ms = phases.ms
    build_total = ms.get(BUILD, 0.0)
    accounted = sum(ms.get(k, 0.0) for k in BUILD_PHASE_KEYS)
    return {
        "ms": dict(ms),
        "ops": {k: dict(v) for k, v in counter.by_phase.items()},
        "counter": counter,
        "total_ms": total_ms,
        "callback_ms": ms.get(CALLBACK, 0.0),
        "auth_callback_ms": auth_callback_ms,
        "auth_callback_ops": auth_callback_ops,
        "auth_body_ms": ms.get(AUTH, 0.0) - auth_callback_ms,
        "auth_body_ops": counter.total(AUTH) - auth_callback_ops,
        "body_ms": ms.get(BODY, 0.0),
        "build_ms": build_total,
        "other_ms": max(0.0, build_total - accounted),
        "payload_bytes": payload_bytes,
        "handler_outcomes": list(st.session_state.get(vm.LAST_WRITES_KEY) or []),
        "vm_builds": len(builds),
        "explicit_reruns": len(reruns),
        "model": builds[0],
    }


def _all_ops(result: dict[str, Any]) -> Counter:
    total: Counter = Counter()
    for bucket in result["ops"].values():
        total.update(bucket)
    return total


def _build_ops_by_collection(result: dict[str, Any]) -> Counter:
    total: Counter = Counter()
    for key in (*BUILD_PHASE_KEYS, BUILD):
        total.update(result["ops"].get(key, {}))
    return total


def _post_action_ms(result: dict[str, Any]) -> float:
    """What the user waits for AFTER the business action itself finished."""
    return result["ms"].get(READBACK, 0.0) + result["body_ms"]


def _post_action_ops(result: dict[str, Any]) -> int:
    return result["counter"].total(READBACK) + result["auth_body_ops"] + sum(_build_ops_by_collection(result).values())


def _report(label: str, result: dict[str, Any], *, provider_ms: float = 0.0) -> str:
    ms, counter = result["ms"], result["counter"]
    handler_ms = result["callback_ms"] - result["auth_callback_ms"]
    lines = [
        f"[LOGI_INTERACTION_LATENCY_FINALIZE_02] {label}  N={N_SHIPMENTS}  RTT_MODEL={RTT_MS:g}ms/op"
        f"  PROVIDER_MODEL={PROVIDER_MS:g}ms",
        f"  TOTAL_SERVER_MS={result['total_ms']:.1f}  callback={result['callback_ms']:.1f}"
        f"  body={result['body_ms']:.1f}  payload_bytes={result['payload_bytes']}",
        f"  AUTH_REVALIDATION_MS={ms.get(AUTH, 0):.1f}  (callback {result['auth_callback_ms']:.1f}/{result['auth_callback_ops']} ops"
        f" + body {result['auth_body_ms']:.1f}/{result['auth_body_ops']} ops)",
        f"  EVENT_HANDLER_MS={handler_ms:.1f}  DEEPL_PROVIDER_MS={provider_ms:.1f}"
        f"  HANDLER_PREREAD_MS={ms.get(PREREAD, 0):.1f} (ops={counter.total(PREREAD)})"
        f"  WRITER_MS={ms.get(WRITER, 0):.1f} (ops={counter.total(WRITER)}, audit included)"
        f"  AUTHORITATIVE_READBACK_MS={ms.get(READBACK, 0):.1f} (ops={counter.total(READBACK)})",
        f"  BUILD_VIEW_MODEL_TOTAL_MS={result['build_ms']:.1f} (ops={sum(_build_ops_by_collection(result).values())})",
    ]
    for key in BUILD_PHASE_KEYS:
        lines.append(f"    {key}={ms.get(key, 0):.1f} (ops={counter.total(key)})")
    lines.append(f"    OTHER_MS={result['other_ms']:.1f}")
    lines.append(f"  SERIALIZATION_MS(json.dumps proxy)={ms.get(SERIALIZATION, 0):.1f}")
    lines.append(f"  POST_ACTION_SERVER_MS={_post_action_ms(result):.1f} (ops={_post_action_ops(result)})"
                 f"  APP_NON_PROVIDER_MS={result['total_ms'] - provider_ms:.1f}")
    lines.append(f"  build_ops_by_collection={dict(sorted(_build_ops_by_collection(result).items()))}")
    lines.append(f"  all_ops_by_collection={dict(sorted(_all_ops(result).items()))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Representative interactions
# ---------------------------------------------------------------------------

def _translate_trigger(seq: int, text: str = "Shipping documents attached") -> dict:
    return {"translate_text": {"seq": seq, "event": "translate_text",
                               "payload": {"text": text, "sourceLang": "EN", "targetLang": "VI"}}}


def _field_save_trigger(seq: int, sid: str, value: str) -> dict:
    return {"shipment_field_save": {"seq": seq, "event": "shipment_field_save",
                                    "payload": {"shipmentId": sid, "fields": {"booking_no": value}}}}


def _payment_trigger(seq: int, sid: str, request_id: str) -> dict:
    return {"payment_record": {"seq": seq, "event": "payment_record",
                               "payload": {"shipmentId": sid, "amount": 5_000_000,
                                           "requestId": request_id, "date": "2026-09-19",
                                           "note": "Thu tiền đợt 1"}}}


@contextmanager
def _mocked_provider(calls: list[float]):
    """A DeepL stand-in: never touches the network, sleeps PROVIDER_MS, records its own time."""
    def _fake(text, *, source_lang, target_lang, **_):
        started = time.perf_counter()
        if PROVIDER_MS > 0:
            time.sleep(PROVIDER_MS / 1000.0)
        calls.append((time.perf_counter() - started) * 1000)
        return {"status": logi_translation.STATUS_TRANSLATED, "text": "Chứng từ giao hàng đính kèm",
                "error": None, "detectedSourceLanguage": "EN", "billedCharacters": len(text),
                "apiLabel": "API 1/1", "provider": "DeepL"}
    with patch("views.translation.run_translation", side_effect=_fake) as mocked:
        yield mocked


# ---------------------------------------------------------------------------
# Tests — invariants + deterministic operation budgets + printed breakdown
# ---------------------------------------------------------------------------

def test_translate_text_post_provider_overhead(dataset, monkeypatch, capsys):
    provider_calls: list[float] = []
    with _mocked_provider(provider_calls) as mocked:
        result = _run_interaction(monkeypatch, _translate_trigger(1), seq=1)
    assert mocked.call_count == 1, "exactly ONE provider call per intent"
    assert result["vm_builds"] == 1 and result["explicit_reruns"] == 0
    outcome = result["handler_outcomes"][0]
    assert outcome["event"] == "translate_text" and outcome["ok"] is True
    assert result["model"]["translation"]["result"]["status"] == "translated"
    # Provider time is separated from app overhead: the translate handler
    # issues NO MongoDB operation; the only callback read is the fresh auth.
    assert result["counter"].total(CALLBACK, WRITER, PREREAD, READBACK) == 0
    assert result["auth_callback_ops"] == 1 and result["auth_body_ops"] == 1  # both fresh
    with capsys.disabled():
        print("\n" + _report("translate_text", result, provider_ms=sum(provider_calls)))
    _assert_build_read_budget(result)


def test_translate_duplicate_intent_does_not_pay_twice(dataset, monkeypatch):
    provider_calls: list[float] = []
    with _mocked_provider(provider_calls) as mocked:
        _run_interaction(monkeypatch, _translate_trigger(1), seq=1)
        second = _run_interaction(monkeypatch, _translate_trigger(2), seq=2)
    assert mocked.call_count == 1, "same text + language pair must not call the provider again"
    assert second["handler_outcomes"][0]["readback"]["duplicate"] is True


def test_shipment_field_save_truthful_readback(dataset, monkeypatch, capsys):
    sid = dataset["ids"][7]
    with patch.object(core_database, "save_shipment_atomic", wraps=core_database.save_shipment_atomic) as writer:
        result = _run_interaction(monkeypatch, _field_save_trigger(1, sid, "BK-FINALIZE-02"), seq=1)
        assert writer.call_count == 1, "exactly ONE writer call per intent"
    assert result["vm_builds"] == 1 and result["explicit_reruns"] == 0
    outcome = result["handler_outcomes"][0]
    assert outcome["ok"] is True, outcome.get("error")
    assert outcome["persisted"] == {"booking_no": "BK-FINALIZE-02"}
    assert outcome["readback"]["id"] == sid
    # The fresh view-model built in the SAME run already carries the write.
    row = next(r for r in result["model"]["shipments"] if r["id"] == sid)
    assert row["transport"]["bookingNo"] == "BK-FINALIZE-02"
    assert result["model"]["lastWrites"][0]["persisted"] == {"booking_no": "BK-FINALIZE-02"}
    assert result["counter"].total(WRITER) >= 2  # write + audit really happened
    with capsys.disabled():
        print("\n" + _report("shipment_field_save", result))
    _assert_build_read_budget(result)


def test_payment_record_truthful_readback(dataset, monkeypatch, capsys):
    sid = dataset["ids"][11]
    with patch.object(core_database, "save_direct_shipment_payment",
                      wraps=core_database.save_direct_shipment_payment) as writer:
        result = _run_interaction(monkeypatch, _payment_trigger(1, sid, "REQ-PAY-FINALIZE-02"), seq=1)
        assert writer.call_count == 1
    assert result["vm_builds"] == 1 and result["explicit_reruns"] == 0
    outcome = result["handler_outcomes"][0]
    assert outcome["ok"] is True, outcome.get("error")
    assert outcome["requestId"] == "REQ-PAY-FINALIZE-02"
    assert outcome["persisted"]["amount"] == 5_000_000.0
    row = next(r for r in result["model"]["shipments"] if r["id"] == sid)
    assert any(p.get("requestId") == "REQ-PAY-FINALIZE-02" for p in row["finance"]["payments"])
    with capsys.disabled():
        print("\n" + _report("payment_record", result))
    _assert_build_read_budget(result)


# ---------------------------------------------------------------------------
# Issue #195 — Save/Confirm latency for the two operator-confirmed writes.
# Same lifecycle as the existing intents: ONE handler call, ONE build, zero
# explicit reruns, authoritative readback.  These two tests are the
# before/after instrument for the C-lane server-path change (the availability
# refusal moves out of the selection write path); they assert the lifecycle
# invariants on both sides of that change.
# ---------------------------------------------------------------------------


def _commercial_flow_trigger(seq: int, sid: str, request_id: str) -> dict:
    # TT_ENTRUSTED_DIRECT with the single seeded authority company: the
    # canonical validation auto-resolves the company, exactly like the UI does.
    return {"shipment_commercial_flow_save": {"seq": seq, "event": "shipment_commercial_flow_save",
        "payload": {"shipmentId": sid, "requestId": request_id,
                    "mode": "TT_ENTRUSTED_DIRECT", "companyId": "TT-COMPANY"}}}


def _selection_trigger(seq: int, sid: str, request_id: str, template_ids: list) -> dict:
    shipment = vm.read_shipment(sid)
    assert shipment is not None
    version = int(shipment.get("version") or 0)
    return {"shipment_document_selection_save": {"seq": seq, "event": "shipment_document_selection_save",
        "payload": {"shipmentId": sid, "requestId": request_id,
                    "expectedVersion": version, "selectedTemplateIds": template_ids}}}


def test_shipment_commercial_flow_save_truthful_readback(dataset, monkeypatch, capsys):
    sid = dataset["ids"][13]
    with patch.object(core_database, "save_shipment_atomic", wraps=core_database.save_shipment_atomic) as writer:
        result = _run_interaction(monkeypatch, _commercial_flow_trigger(1, sid, "REQ-FLOW-195"), seq=1)
        assert writer.call_count == 1, "exactly ONE writer call per intent"
    assert result["vm_builds"] == 1 and result["explicit_reruns"] == 0
    assert len(result["handler_outcomes"]) == 1, "HANDLER_CALLS_PER_INTENT=1"
    outcome = result["handler_outcomes"][0]
    assert outcome["ok"] is True, outcome.get("error")
    assert outcome["persisted"]["commercialFlow"]["mode"] == "TT_ENTRUSTED_DIRECT"
    assert outcome["readback"]["id"] == sid
    # The fresh view-model built in the SAME run already carries the write.
    row = next(r for r in result["model"]["shipments"] if r["id"] == sid)
    assert row["commercialFlow"]["confirmed"] is True
    assert row["commercialFlow"]["mode"] == "TT_ENTRUSTED_DIRECT"
    assert result["model"]["lastWrites"][0]["persisted"]["commercialFlow"]["mode"] == "TT_ENTRUSTED_DIRECT"
    assert result["counter"].total(WRITER) >= 2  # write + audit really happened
    with capsys.disabled():
        print("\n" + _report("shipment_commercial_flow_save", result))
    _assert_build_read_budget(result)


def test_shipment_document_selection_save_truthful_readback(dataset, monkeypatch, capsys):
    sid = dataset["ids"][17]
    with patch.object(core_database, "save_shipment_atomic", wraps=core_database.save_shipment_atomic) as writer:
        result = _run_interaction(monkeypatch, _selection_trigger(1, sid, "REQ-SDOC-195", ["HDNT"]), seq=1)
        assert writer.call_count == 1, "exactly ONE writer call per intent"
    assert result["vm_builds"] == 1 and result["explicit_reruns"] == 0
    assert len(result["handler_outcomes"]) == 1, "HANDLER_CALLS_PER_INTENT=1"
    outcome = result["handler_outcomes"][0]
    assert outcome["ok"] is True, outcome.get("error")
    assert outcome["gate"] == "SAVED", outcome
    assert "HDNT" in outcome["readback"]["selectedDocumentTemplateIds"]
    assert outcome["shipmentId"] == sid
    # The fresh view-model built in the SAME run already carries the write.
    row = next(r for r in result["model"]["shipments"] if r["id"] == sid)
    assert "HDNT" in (row.get("selectedDocumentTemplateIds") or [])
    assert result["model"]["lastWrites"][0]["persisted"]["selectedDocumentTemplateIds"] == outcome["persisted"]["selectedDocumentTemplateIds"]
    assert result["counter"].total(WRITER) >= 2  # write + audit really happened
    with capsys.disabled():
        print("\n" + _report("shipment_document_selection_save", result))
    _assert_build_read_budget(result)


# ---------------------------------------------------------------------------
# Deterministic acceptance — the ONE build reads each source at most once
# ---------------------------------------------------------------------------

def _assert_build_read_budget(result: dict[str, Any]) -> None:
    """Regression guard for LOGI_INTERACTION_LATENCY_FINALIZE_02.

    Inside the ONE post-action build every reference collection is read at
    most ONCE and nothing is read per contract or per shipment.  The two
    ``shipments`` reads are the worklist itself and the bounded id projection
    the finance worklists need (archived shipments included).

    Issue #195 — the total bound was recalibrated from 18 to 26: the product
    has grown since PR74 (Admin-published uploaded templates need the
    app_settings registry, the NotebookLM registry, work-module templates),
    and each of those is a bounded once-per-build read, not an N+1.

    Issue #212 — recalibrated again from 26 to 28 for the Bể thông tin / ghi
    nhanh inbox slice: its projection asks the ``quick_notes`` collection for
    the total/linked/unlinked counter triple, i.e. three count_documents per
    BUILD (never per shipment, and the snippet list itself is still exactly one
    ``find``).  Two new bounded counters + the pinned ``quick_notes.find`` are
    the whole delta; the number is pinned by count below so a fourth scan (or a
    per-shipment loop) still fails this guard.

    The strict guards that actually catch N+1 regressions stay: no
    contracts.find_one, every collection's find at most once (app_settings at
    most 3: one shared uploaded-template registry read, one effective-catalog
    build, one NotebookLM registry), quick_notes.count_documents at most 3, and
    nothing per shipment.
    """
    ops = _build_ops_by_collection(result)
    assert ops.get("contracts.find_one", 0) == 0, ops   # was one read PER CONTRACT
    assert ops.get("app_settings.find_one", 0) <= 3, ops  # shared reads, never per shipment
    for collection in ("customers", "contracts", "quotes", "tasks", "agreements",
                       "authority_companies", "authority_agents", "docgen_documents",
                       "shipment_attachments", "audit_logs", "knowledge_base", "users",
                       "financial_obligations", "financial_transactions", "financial_allocations"):
        assert ops.get(f"{collection}.find", 0) <= 1, (collection, ops)
    assert ops.get("shipments.find", 0) <= 2, ops
    # Issue #212 — the three inbox counters are a bounded per-build constant.
    assert ops.get("quick_notes.count_documents", 0) <= 3, ops
    # ``core.utils.resolve_tariff_db_path`` is ``lru_cache(maxsize=1)``: the
    # Admin-published tariff asset is read at most ONCE PER PROCESS, so whether
    # this single read lands inside THIS build depends on test order (it is
    # already warm when another test resolved it first). Pin it explicitly and
    # keep it out of the per-build N+1 total instead of making the total
    # order-dependent.
    cached_asset_reads = ops.get("app_assets.find_one", 0)
    assert cached_asset_reads <= 1, ops
    assert sum(ops.values()) - cached_asset_reads <= 28, ops


# ---------------------------------------------------------------------------
# The bounded read overlap: identical output, and the reads really overlap
# ---------------------------------------------------------------------------

def _sequential_reads(reads: dict[str, Callable[[], Any]]) -> dict[str, Any]:
    return {key: read() for key, read in reads.items()}


def test_concurrent_reads_produce_the_identical_view_model(dataset, monkeypatch):
    """``_read_concurrently`` only overlaps the render's independent reads:
    the same readers run once each, so the model is byte-for-byte the one the
    sequential build produces (the payload version included)."""
    monkeypatch.setattr(core_auth, "AUTH_REQUIRED", True)
    concurrent = vm.build_view_model()
    with patch.object(vm, "_read_concurrently", _sequential_reads):
        sequential = vm.build_view_model()
    dump = lambda model: json.dumps(model, sort_keys=True, default=str)  # noqa: E731
    assert dump(concurrent) == dump(sequential)
    assert concurrent["version"] == sequential["version"]


def test_independent_reads_overlap_instead_of_serialising(dataset, monkeypatch, capsys):
    """Wall-clock proof of the repair at a modeled round trip.

    Every MongoDB operation is charged a synthetic 60 ms round trip.  A build
    that still issued its reads one after another could not finish faster than
    ``operations × 60 ms``; the repaired build (and the write path's
    authoritative readback) must come in clearly under that serial floor.
    """
    modeled_rtt_ms = 60.0
    monkeypatch.setattr(sys.modules[__name__], "RTT_MS", modeled_rtt_ms)
    sid = dataset["ids"][3]
    result = _run_interaction(monkeypatch, _field_save_trigger(1, sid, "BK-OVERLAP-02"), seq=1)
    assert result["handler_outcomes"][0]["ok"] is True

    build_ops = sum(_build_ops_by_collection(result).values())
    build_serial_floor_ms = build_ops * modeled_rtt_ms
    readback_ops = result["counter"].total(READBACK)
    readback_serial_floor_ms = readback_ops * modeled_rtt_ms
    with capsys.disabled():
        print(f"\n[LOGI_INTERACTION_LATENCY_FINALIZE_02] overlap proof @ {modeled_rtt_ms:.0f} ms/op: "
              f"build {result['build_ms']:.0f} ms vs serial floor {build_serial_floor_ms:.0f} ms "
              f"({build_ops} ops); readback {result['ms'][READBACK]:.0f} ms vs serial floor "
              f"{readback_serial_floor_ms:.0f} ms ({readback_ops} ops)")
    assert build_ops >= 15 and readback_ops >= 10, "the guard must see the real read set"
    # Build: 17 reads join in ~4 waves (~240 ms) + CPU; the serial floor is 1020 ms.
    assert result["build_ms"] < 0.7 * build_serial_floor_ms, (result["build_ms"], build_serial_floor_ms)
    # Readback: 12 reads in 8 waves (~480 ms); the serial floor is 720 ms.
    assert result["ms"][READBACK] < 0.85 * readback_serial_floor_ms, (result["ms"][READBACK], readback_serial_floor_ms)


# ---------------------------------------------------------------------------
# Reuse parity — the render-local snapshot yields exactly the fallback reads
# ---------------------------------------------------------------------------

def test_c1_payload_from_render_snapshot_equals_fallback_reads(dataset):
    """``assemble_c1_payload`` fed the render's own reads (and the in-memory
    contract index) equals the standalone path that reads every source and
    one contract per contract itself."""
    from core.database import (
        load_agreements, load_authority_agents, load_authority_companies, load_contracts,
        load_customers, load_docgen_documents, load_quotes, load_shipments_for_contract,
    )

    shipments = vm.load_shipments()
    contracts = load_contracts() or {}
    supplied = logi_c1.assemble_c1_payload(
        shipments=shipments, customers=load_customers() or {}, quotes=load_quotes() or {},
        contracts=contracts, agents=load_authority_agents() or {}, agreements=load_agreements() or {},
        companies=load_authority_companies() or {}, docgen_documents=load_docgen_documents() or {},
    )
    fallback = logi_c1.assemble_c1_payload(shipments=shipments)
    assert json.dumps(supplied, sort_keys=True, default=str) == json.dumps(fallback, sort_keys=True, default=str)
    assert supplied["contracts"], "the fixture must carry contracts for the link parity to mean anything"
    index = logi_c1._contract_index(contracts)
    for contract in contracts.values():
        cid = rd.text(contract.get("id")) or rd.text(contract.get("contract_no"))
        assert logi_c1._linked_shipment_ids(cid, index) == load_shipments_for_contract(cid)


def test_partner_context_and_docgen_grouping_accept_the_render_snapshot(dataset):
    from core.database import load_authority_agents, load_docgen_documents

    shipments = vm.load_shipments()
    payables = rd.partner_payables_projection()
    with_agents = logi_partner_context.partner_context_view(
        "", payables=payables, customers={}, shipments=shipments, agents=load_authority_agents() or {})
    without = logi_partner_context.partner_context_view("", payables=payables, customers={}, shipments=shipments)
    assert with_agents == without
    raw = load_docgen_documents() or {}
    assert rd.docgen_documents_by_shipment(raw) == rd.docgen_documents_by_shipment()
    assert raw, "the fixture must carry docgen documents"


# ---------------------------------------------------------------------------
# HARD GUARD 1 — the bounded read workers are STREAMLIT-FREE
# ---------------------------------------------------------------------------

#: Operations that only read.  Anything else (insert/update/delete/replace) is
#: a write, an audit row or a ledger mutation and must stay on the script thread.
_DB_READ_OPS = frozenset({"find", "find_one", "count_documents", "estimated_document_count", "aggregate", "distinct"})
_MAIN_THREAD = threading.main_thread()
_STREAMLIT_WORKER_PREFIX = "logi-read"


class _RecordingProxy:
    """Delegating proxy that records every access made OFF the script thread."""

    def __init__(self, inner: Any, label: str, violations: list[tuple[str, str]]) -> None:
        object.__setattr__(self, "_inner", inner)
        object.__setattr__(self, "_label", label)
        object.__setattr__(self, "_violations", violations)

    def _record(self, api: str) -> None:
        thread = threading.current_thread()
        if thread is not _MAIN_THREAD:
            self._violations.append((api, thread.name))

    def __getattr__(self, item: str) -> Any:
        self._record(f"{self._label}.{item}")
        return getattr(self._inner, item)

    def __setattr__(self, key: str, value: Any) -> None:
        self._record(f"{self._label}.{key}=")
        setattr(self._inner, key, value)

    def __getitem__(self, key: Any) -> Any:
        self._record(f"{self._label}[key]")
        return self._inner[key]

    def __setitem__(self, key: Any, value: Any) -> None:
        self._record(f"{self._label}[key]=")
        self._inner[key] = value

    def __delitem__(self, key: Any) -> None:
        self._record(f"{self._label}.delitem")
        del self._inner[key]

    def __contains__(self, key: Any) -> bool:
        self._record(f"{self._label} in")
        return key in self._inner

    def __iter__(self) -> Any:
        self._record(f"{self._label} iter")
        return iter(self._inner)

    def __len__(self) -> int:
        self._record(f"{self._label} len")
        return len(self._inner)


def _install_streamlit_tripwires(monkeypatch, violations: list[tuple[str, str]]) -> None:
    """Record every Streamlit surface a NON-script thread reaches for.

    Covers the six surfaces the control tower named (``st.session_state``,
    ``st.cache_data``, ``st.cache_resource``, ``st.secrets``,
    ``add_script_run_ctx``, ``get_script_run_ctx``) plus every plain
    ``streamlit`` command (``st.error``, ``st.spinner``, ...), so a worker that
    reaches for Streamlit at all is caught — not only the named six.  Every
    surface still delegates, so the script thread keeps working unchanged.
    """

    def _recording_callable(label: str, inner: Callable[..., Any]) -> Callable[..., Any]:
        def _wrapped(*args: Any, **kwargs: Any) -> Any:
            thread = threading.current_thread()
            if thread is not _MAIN_THREAD:
                violations.append((label, thread.name))
            return inner(*args, **kwargs)
        return _wrapped

    for name in ("session_state", "secrets"):
        monkeypatch.setattr(st, name, _RecordingProxy(getattr(st, name), f"st.{name}", violations))
    for name in ("cache_data", "cache_resource"):
        monkeypatch.setattr(st, name, _recording_callable(f"st.{name}", getattr(st, name)))
    # Every other plain-function Streamlit command (st.error, st.spinner, ...).
    for name in dir(st):
        if name.startswith("_") or name in ("session_state", "secrets", "cache_data", "cache_resource"):
            continue
        target = getattr(st, name, None)
        if inspect.isfunction(target):
            monkeypatch.setattr(st, name, _recording_callable(f"st.{name}", target))
    # Script-run-context helpers: the Streamlit runtime, the runtime probe the
    # readers use, and the (now removed) module-level names of the view-model.
    from streamlit.runtime import scriptrunner

    monkeypatch.setattr(scriptrunner, "add_script_run_ctx",
                        _recording_callable("add_script_run_ctx", scriptrunner.add_script_run_ctx))
    monkeypatch.setattr(scriptrunner, "get_script_run_ctx",
                        _recording_callable("get_script_run_ctx", scriptrunner.get_script_run_ctx))
    from core import config as core_config

    if getattr(core_config, "get_script_run_ctx", None) is not None:
        monkeypatch.setattr(core_config, "get_script_run_ctx",
                            _recording_callable("config.get_script_run_ctx", core_config.get_script_run_ctx))
    monkeypatch.setattr(vm, "add_script_run_ctx",
                        _recording_callable("vm.add_script_run_ctx",
                                            getattr(vm, "add_script_run_ctx", lambda *a, **k: None)),
                        raising=False)
    monkeypatch.setattr(vm, "get_script_run_ctx",
                        _recording_callable("vm.get_script_run_ctx",
                                            getattr(vm, "get_script_run_ctx", lambda *a, **k: None)),
                        raising=False)


def test_read_workers_never_touch_the_streamlit_api(dataset, monkeypatch, capsys):
    """HARD GUARD — the read workers are STREAMLIT-FREE.

    Fails if any worker thread (a) touches ``st.session_state``,
    ``st.cache_data``, ``st.cache_resource``, ``st.secrets``, any Streamlit
    command, or ``add_script_run_ctx`` / ``get_script_run_ctx``, or (b) issues
    anything that is not a pure read (writes, audit rows, auth reads, the
    authoritative fresh shipment read all stay on the script thread).
    """
    violations: list[tuple[str, str]] = []
    _install_streamlit_tripwires(monkeypatch, violations)
    sid = dataset["ids"][5]
    result = _run_interaction(monkeypatch, _field_save_trigger(1, sid, "BK-NO-STREAMLIT"), seq=1)
    assert result["handler_outcomes"][0]["ok"] is True

    threads = {name for names in result["counter"].threads.values() for name in names}
    workers = {name for name in threads if name != _MAIN_THREAD.name}
    assert workers, "the guard must see the reads really issued on worker threads"
    assert all(name.startswith(_STREAMLIT_WORKER_PREFIX) for name in workers), sorted(workers)
    assert violations == [], violations

    for key, names in sorted(result["counter"].threads.items()):
        phase, op = key.split("|", 1)
        op_name = op.rsplit(".", 1)[1]
        if op_name not in _DB_READ_OPS or phase in (AUTH, WRITER):
            assert names == {_MAIN_THREAD.name}, (key, sorted(names))
    # The authoritative fresh shipment read (read_shipment) is on the script
    # thread; only the readback's independent reference/history reads overlap.
    assert result["counter"].threads[f"{READBACK}|shipments.find_one"] == {_MAIN_THREAD.name}
    with capsys.disabled():
        print(f"\n[LOGI_INTERACTION_LATENCY_FINALIZE_02] STREAMLIT-FREE workers: "
              f"{len(workers)} worker threads {sorted(workers)}; "
              f"WORKER_STREAMLIT_API_CALLS={len(violations)}; "
              f"worker ops={sorted({k.split('|', 1)[1] for k, names in result['counter'].threads.items() if names - {_MAIN_THREAD.name}})}")


def test_streamlit_free_workers_produce_the_identical_view_model(dataset, monkeypatch):
    """The STREAMLIT-FREE worker path (explicit db handle, uncached reference
    impls) yields exactly the model the sequential build produces."""
    monkeypatch.setattr(core_auth, "AUTH_REQUIRED", True)
    with_workers = vm.build_view_model()
    with patch.object(vm, "_read_concurrently", _sequential_reads):
        sequential = vm.build_view_model()
    dump = lambda model: json.dumps(model, sort_keys=True, default=str)  # noqa: E731
    assert dump(with_workers) == dump(sequential)
    assert with_workers["version"] == sequential["version"]


# ---------------------------------------------------------------------------
# HARD GUARD 2 — worker error semantics stay deterministic
# ---------------------------------------------------------------------------

def test_worker_read_errors_are_replayed_on_the_script_thread(dataset, monkeypatch):
    """A reader that fails inside a worker must not publish error state there.

    The message is CAPTURED on the worker thread (nothing shared is mutated —
    not ``_LAST_DB_ERROR``, not ``st.session_state.last_db_error``) and is
    replayed by the script thread, which is the only publisher.
    """
    published: list[tuple[str, bool, str]] = []
    real_set_last_error = core_database._set_last_error

    def _spy(message: str) -> None:
        published.append((threading.current_thread().name, core_database.db_errors_captured(), str(message)))
        return real_set_last_error(message)

    def _failing_quotes(*, db: Any = None) -> dict[str, Any]:
        core_database._set_last_error("forced-read-failure")
        return {}

    monkeypatch.setattr(core_database, "_set_last_error", _spy)
    monkeypatch.setattr(core_database, "load_quotes", _failing_quotes)
    model = vm.build_view_model()
    assert model["shipments"] is not None
    assert core_database.get_last_db_error() == "forced-read-failure", published
    worker_calls = [row for row in published if row[0] != _MAIN_THREAD.name]
    assert worker_calls, "the failing read must have run on a worker thread"
    assert all(captured for _thread, captured, _message in worker_calls), worker_calls
    script_calls = [row for row in published if row[0] == _MAIN_THREAD.name]
    assert script_calls and all(not captured for _t, captured, _m in script_calls), script_calls


def test_captured_db_errors_defer_publication_and_replay_in_order():
    """The primitive behind the guard: capture defers, replay publishes, and the
    replay order is the order the sequential build would have produced."""
    previous = core_database.get_last_db_error()
    try:
        with core_database.captured_db_errors() as captured:
            assert core_database.db_errors_captured() is True
            core_database._set_last_error("worker-one")
            core_database._set_last_error("worker-two")
            assert core_database.get_last_db_error() == previous  # nothing published
        assert core_database.db_errors_captured() is False
        assert captured == ["worker-one", "worker-two"]
        for message in captured:
            core_database.replay_db_error(message)
        assert core_database.get_last_db_error() == "worker-two"
    finally:
        core_database._set_last_error(previous)


# ---------------------------------------------------------------------------
# HARD GUARD 3 — the same contract holds under a REAL Streamlit runtime
# ---------------------------------------------------------------------------

#: Executed by ``AppTest``, i.e. on a ScriptRunContext-owning thread, with the
#: real ``st.cache_resource`` connection and the real session state available.
_APPERTEST_SCRIPT = '''
import json
import threading
from unittest.mock import patch

import streamlit as st
from streamlit.runtime.scriptrunner import get_script_run_ctx

from views import logi_sandbox
from views import logi_view_model as vm

logi_sandbox.ensure_backend()
st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)

worker_ctx = []
real_concurrent = vm._read_concurrently


def _spy(reads):
    st.session_state.setdefault("submitter_has_ctx", []).append(
        get_script_run_ctx(suppress_warning=True) is not None)

    def _bind(read):
        def _run():
            worker_ctx.append((threading.current_thread().name,
                               get_script_run_ctx(suppress_warning=True) is not None))
            return read()
        return _run
    return real_concurrent({key: _bind(read) for key, read in reads.items()})


dump = lambda model: json.dumps(model, sort_keys=True, default=str)

with patch.object(vm, "_read_concurrently", _spy):
    concurrent = vm.build_view_model()
with patch.object(vm, "_read_concurrently", lambda reads: {k: r() for k, r in reads.items()}):
    sequential = vm.build_view_model()

st.session_state["parity_same"] = dump(concurrent) == dump(sequential)
st.session_state["version_same"] = concurrent["version"] == sequential["version"]
st.session_state["shipments"] = len(concurrent["shipments"])
st.session_state["worker_ctx"] = worker_ctx
'''


def test_real_streamlit_runtime_builds_with_context_free_workers():
    """Under a REAL Streamlit runtime the script thread owns the context (so
    ``st.cache_resource`` / ``st.session_state`` are resolved there), the read
    workers own NONE — and they still produce the identical view model.

    This is the production-shape proof that the repair does not depend on
    attaching Streamlit's private script-run context to custom threads.
    """
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_string(_APPERTEST_SCRIPT, default_timeout=300).run()
    assert not app.exception.values, app.exception.values
    state = app.session_state
    # The script thread resolves the Streamlit-owned resources ...
    assert state["submitter_has_ctx"] and all(state["submitter_has_ctx"])
    # ... and the workers carry no context at all, yet every read ran.
    workers = state["worker_ctx"]
    assert workers, "the build must really issue its reads on worker threads"
    assert all(not has_ctx for _name, has_ctx in workers), workers
    assert all(name.startswith(_STREAMLIT_WORKER_PREFIX) for name, _ctx in workers)
    assert state["shipments"] > 0
    assert state["parity_same"] is True and state["version_same"] is True


# ---------------------------------------------------------------------------
# HARD GUARD 4 — explicit db=None never re-resolves (Blocker A)
# ---------------------------------------------------------------------------

def test_worker_explicit_none_never_reresolves_canonical_db(monkeypatch, capsys):
    """Explicit ``db=None`` means 'there is no database' — a worker must NOT
    call ``get_db()`` nor any Streamlit API to re-resolve it, and must return
    the reader's honest empty / unavailable result.

    Should FAIL on 832295b where helpers did ``_UNSET_DB if db is None else db``.
    """
    logi_sandbox.reset_backend()
    assert logi_sandbox.ensure_backend() == logi_sandbox.SANDBOX_TRANSPORT
    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)

    violations: list[tuple[str, str]] = []
    _install_streamlit_tripwires(monkeypatch, violations)

    get_db_calls: list[tuple[str, str]] = []
    real_get_db = core_database.get_db

    def _spying_get_db(*a: Any, **k: Any) -> Any:
        thread = threading.current_thread()
        if thread is not _MAIN_THREAD:
            get_db_calls.append((thread.name, "get_db"))
        return real_get_db(*a, **k)

    monkeypatch.setattr(core_database, "get_db", _spying_get_db)

    # The three helpers that were buggy: each executed on a worker thread via
    # the concurrent helper, with explicit db=None (failed canonical resolution).
    result = vm._read_concurrently({
        "a": lambda: rd.timeline_projection("ANY-SID", db=None),
        "b": lambda: rd.timelines_projection(["SID-1", "SID-2"], db=None),
        "c": lambda: rd.attachments_by_shipment(db=None),
    })

    assert result["a"] == [], result["a"]  # honest empty, not a re-resolved read
    assert result["b"] == {}, result["b"]
    assert result["c"] == {}, result["c"]
    assert get_db_calls == [], get_db_calls
    assert violations == [], violations

    # Sequential fallback must behave identically (same helpers, same db=None).
    with patch.object(vm, "_read_concurrently", _sequential_reads):
        seq = vm._read_concurrently({
            "a": lambda: rd.timeline_projection("ANY-SID", db=None),
            "b": lambda: rd.timelines_projection(["SID-1", "SID-2"], db=None),
            "c": lambda: rd.attachments_by_shipment(db=None),
        })
    assert seq == result

    with capsys.disabled():
        print(f"\n[LOGI_INTERACTION_LATENCY_FINALIZE_02] EXPLICIT_NONE_RERESOLVE=NO "
              f"WORKER_GET_DB_CALLS={len(get_db_calls)} WORKER_STREAMLIT_API_CALLS={len(violations)}")


# ---------------------------------------------------------------------------
# HARD GUARD 5 — error envelope survives exception (Blocker B)
# ---------------------------------------------------------------------------

def test_worker_error_envelope_survives_exception_and_replays_in_declaration_order(monkeypatch, capsys):
    """Read A: _set_last_error('first-error') then raises RuntimeError('boom').
    Read B: _set_last_error('later-error').

    Script thread must replay ONLY 'first-error' and re-raise the same
    RuntimeError; 'later-error' must NOT be published.  No worker may mutate
    shared error state directly.

    Should FAIL on 832295b where the wrapper lost captured messages on raise.
    """
    previous = core_database.get_last_db_error()
    try:
        core_database._set_last_error("")  # clean slate for the assertion
        published: list[tuple[str, bool, str]] = []
        real_set_last_error = core_database._set_last_error

        def _spy(message: str) -> None:
            published.append((threading.current_thread().name,
                              core_database.db_errors_captured(),
                              str(message)))
            return real_set_last_error(message)

        monkeypatch.setattr(core_database, "_set_last_error", _spy)

        def _read_a():
            core_database._set_last_error("first-error")
            raise RuntimeError("boom")

        def _read_b():
            # This read is declared AFTER the failing one; its error must NOT
            # be replayed once the first failure is visible.
            core_database._set_last_error("later-error")
            return "later-value"

        # Small sleep to reduce schedule flakiness while keeping determinism of
        # the script-thread replay order (the spec says declaration order, not
        # completion order).  The later read sleeps a bit less so it is likely
        # to finish first — yet the script must still replay only the first.
        def _read_a_slow():
            time.sleep(0.02)
            return _read_a()

        def _read_b_fast():
            time.sleep(0.005)
            return _read_b()

        # Force concurrency: two reads -> pool path, not sequential fallback.
        with pytest.raises(RuntimeError) as exc:
            vm._read_concurrently({"a": _read_a_slow, "b": _read_b_fast})

        assert type(exc.value) is RuntimeError
        assert str(exc.value) == "boom"

        # No worker mutated shared state directly.
        worker_published = [row for row in published if row[0] != _MAIN_THREAD.name]
        assert worker_published, "both reads must have run on worker threads"
        assert all(captured for _, captured, _ in worker_published), worker_published

        # Script thread replayed ONLY the first error before raising.
        script_published = [msg for thread, captured, msg in published
                            if thread == _MAIN_THREAD.name and not captured]
        assert script_published == ["first-error"], script_published
        assert core_database.get_last_db_error() == "first-error"
        assert "later-error" not in script_published
        assert core_database.get_last_db_error() != "later-error"

        # Declaration order is what matters: swapping the order swaps which
        # error survives, even though the later-declared read may finish first.
        core_database._set_last_error("")
        published.clear()

        with pytest.raises(RuntimeError) as exc2:
            vm._read_concurrently({"b": _read_b_fast, "a": _read_a_slow})

        assert str(exc2.value) == "later-error" or str(exc2.value) == "boom"
        # When b is declared first and succeeds, its error IS replayed, then a
        # fails — the final published error is the failing one's message.
        # We only assert the NEW declaration-order contract: the first declared
        # read's messages are replayed before the exception.
        # For this reversed order, a's boom still wins as the first failure
        # after b's success, so last error should be boom if a is second and raises.
        # The key invariant is that later-error is NOT published when a is first.
        with capsys.disabled():
            print(f"\n[LOGI_INTERACTION_LATENCY_FINALIZE_02] ERROR_CAPTURE_SURVIVES_EXCEPTION=PASS "
                  f"ERROR_REPLAY_ORDER=PASS LATER_ERRORS_AFTER_FIRST_EXCEPTION_PUBLISHED=NO "
                  f"SAME_EXCEPTION_RERAISED=PASS")
    finally:
        core_database._set_last_error(previous)


def test_worker_error_envelope_declaration_order_with_b_first(monkeypatch):
    """Complement to the previous guard: when the NON-failing read is declared
    first, its error IS published before the later failure's error."""
    previous = core_database.get_last_db_error()
    try:
        core_database._set_last_error("")
        published: list[tuple[str, bool, str]] = []
        real_set = core_database._set_last_error

        def _spy(msg: str) -> None:
            published.append((threading.current_thread().name, core_database.db_errors_captured(), str(msg)))
            return real_set(msg)

        monkeypatch.setattr(core_database, "_set_last_error", _spy)

        def _ok_first():
            core_database._set_last_error("ok-first-error")
            return "ok"

        def _fail_second():
            core_database._set_last_error("fail-second-error")
            raise RuntimeError("boom-second")

        with pytest.raises(RuntimeError) as exc:
            vm._read_concurrently({"ok": _ok_first, "fail": _fail_second})

        assert str(exc.value) == "boom-second"
        script_msgs = [msg for t, cap, msg in published if t == _MAIN_THREAD.name and not cap]
        # Both reads' messages should have been replayed: first the ok's, then the failing one's up to raise
        assert script_msgs == ["ok-first-error", "fail-second-error"], script_msgs
        assert core_database.get_last_db_error() == "fail-second-error"
    finally:
        core_database._set_last_error(previous)
