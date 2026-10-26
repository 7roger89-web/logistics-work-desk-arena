"""LOGI_REAL_DATA_RENDER_PERFORMANCE_01 — one render, one read per source.

ROOT CAUSE (independently inspected on ``main``, reproduced here as evidence)
-----------------------------------------------------------------------------
``views.logi_view_model.build_view_model()`` projected every shipment through
readers that each re-fetched COMPLETE Mongo collections:

* ``shipment_projection`` → ``finance_projection`` → ``_partner_projection``
  → ``core.financial_ledger.shipment_partner_position`` → ``_all()`` of
  ``financial_obligations`` + ``financial_transactions`` +
  ``financial_allocations``   (3 reads × N shipments)
* ``shipment_projection`` → ``pxk_projection`` → ``_pxk_document``
  → ``load_docgen_documents(shipment_id)``   (1 read × N)
* ``shipment_projection`` → ``pxk_projection`` → ``load_contracts_for_shipment``
  → full ``contracts`` scan   (1 read × N when no direct contract match)
* ``build_view_model`` → ``timeline_projection(sid)`` → ``load_audit_logs``
  (1 read × N)
* then ``partner_payables_projection()`` AND ``reconciliation_view()`` each
  re-read all three ledger collections for every shipment id, and C1 reloaded
  the whole ``shipments`` collection the render already had.

At N = 95 that is >1000 collection reads for ONE render, which is why mock/small
data felt instant and real Atlas data did not.

WHAT THIS TEST PROVES (deterministic query/read counts, not timings)
--------------------------------------------------------------------
A. the three ledger collections are read O(1) per render, and the old
   per-shipment pattern is demonstrably O(N) on the same fixture;
B. audit history is ONE bounded bulk read, not one read per shipment;
C. canonical docgen metadata is ONE read, not one read per shipment;
D. the render does not reload the full ``shipments`` collection through C1;
E. OUTPUT EQUIVALENCE — the snapshotted fast path and the unchanged per-call
   reader path produce identical projections, with UNKNOWN ≠ ZERO and currency
   separation intact.

Transport: the isolated staging database (mongomock) running the CURRENT
canonical readers and writers unchanged. No production/pilot database and no
real Atlas connection is involved anywhere in this file.
"""

from __future__ import annotations

import time
from collections import Counter
from contextlib import contextmanager

import pytest

from core import database as core_database
from core.financial_ledger import (
    ALLOCATIONS,
    OBLIGATIONS,
    TRANSACTIONS,
    allocate_transaction,
    load_ledger_snapshot,
    save_obligation,
    save_transaction,
    shipment_partner_position,
)
from views import logi_c1
from views import logi_real_data as rd
from views import logi_sandbox
from views import logi_view_model as vm
from views import reconciliation_desk as logi_reconciliation


N_SHIPMENTS = 95
PXK_SHIPMENT = "LO-0460"
LEDGER_SHIPMENT = "LO-0308"
PARTNER_MASTER = "AGT-PHUANH"        # resolves through the authority_agents master
PARTNER_UNLISTED = "AGT-NGOAIDANH"   # no master record → canonical ledger name
COMPANY = "CONG-TY-TRUONG-THANH"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def staging():
    """Clean isolated staging database + deterministic staging actor."""
    import streamlit as st

    logi_sandbox.reset_backend()
    transport = logi_sandbox.ensure_backend()
    assert transport == logi_sandbox.SANDBOX_TRANSPORT
    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)
    yield transport
    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)
    logi_sandbox.reset_backend()


@pytest.fixture()
def event_seq():
    state = {"n": 0}

    def _make(name: str, payload: dict) -> dict:
        state["n"] += 1
        return {name: {"seq": state["n"], "event": name, "payload": payload}}

    return _make


def _dispatch(seq_fn, name, payload):
    outcomes = vm.consume_phase_b_triggers({"seq": 0}, seq_fn(name, payload))
    assert len(outcomes) == 1
    return outcomes[0]


def _real_pxk_document(event_seq) -> str:
    """One REAL docgen document (canonical generator), plus a later revision.

    The first record is produced by the shipped write path — shipment → goods
    line → delivery → ``pxk_generate`` → ``core.docgen.generator`` — so the read
    under test sees a genuine persisted record. A second revision is then added
    in the exact shape that path writes (only ``id`` / revision / file name
    differ), so the shared bulk read must still select the LATEST revision for
    that shipment exactly like the per-shipment reader does.
    """
    sid = PXK_SHIPMENT
    created = _dispatch(event_seq, "shipment_create", {
        "shipmentId": sid, "customerId": "CUST-ANPHAT", "contractId": "HDMB-0306",
        "transport": {"mode": "Truck", "pol": "Bằng Tường", "pod": "Hữu Nghị", "etd": "2026-09-12"},
        "delivery": {"addr": "Kho An Phát — KCN Quế Võ"},
    })
    assert created["ok"], created["error"]
    line = _dispatch(event_seq, "finance_actual_save", {
        "shipmentId": sid,
        "line": {"name": "Hàng tiêu dùng xuất khẩu", "qty": 1, "price": 120000000,
                 "cost": 108000000, "vat": 8},
    })
    assert line["ok"], line["error"]
    confirm = _dispatch(event_seq, "delivery_confirm", {
        "shipmentId": sid, "deliveredAt": "2026-09-12",
        "receiverName": "A. Nam", "receiverTitle": "Thủ kho",
        "deliveryLocation": "Kho An Phát — KCN Quế Võ"})
    assert confirm["ok"], confirm["error"]
    # The commercial-flow gate is a real product requirement (LOGI-193+): PXK
    # generation needs a confirmed flow, so the fixture confirms one through
    # the real shipment_commercial_flow_save event first.
    flow = _dispatch(event_seq, "shipment_commercial_flow_save", {
        "shipmentId": sid, "requestId": "REQ-FIXTURE-FLOW-0460",
        "mode": "TT_ENTRUSTED_DIRECT", "companyId": "TT-COMPANY"})
    assert flow["ok"], flow["error"]
    generated = _dispatch(event_seq, "pxk_generate", {
        "shipmentId": sid, "pxkNo": "PXK-2026-0460", "pxkDate": "2026-09-12"})
    assert generated["ok"], generated

    db = core_database.get_db()
    first = db["docgen_documents"].find_one({"shipment_id": sid}, {"_id": 0})
    assert first is not None and first["document_type"] == "PXK"
    assert first["generation_revision"] == 1

    later = dict(first)
    later["id"] = f"{first['document_id']}::R2"
    later["generation_revision"] = 2
    later["revision"] = 2
    later["output_file_name"] = str(first.get("output_file_name") or "").replace("R1", "R2")
    later["supersedes_document_id"] = first["id"]
    db["docgen_documents"].insert_one(dict(later))
    return sid


def _seed_ledger_records() -> None:
    """Canonical ledger rows for two shipments, via the canonical writers.

    Covers the three shapes the projection must keep distinguishing:
      * one obligation, partially paid by one allocated transaction;
      * two obligations for the SAME partner in DIFFERENT currencies;
      * a partner with no authority_agents master record.
    """
    ok, obligation, error = save_obligation({
        "from_party": {"party_type": "company", "party_id": COMPANY, "name": "Công ty Trường Thành"},
        "to_party": {"party_type": "agent", "party_id": PARTNER_MASTER, "name": "PHÚ ANH"},
        "amount": 57_000_000, "currency": "VND", "purpose": "partner_cost_payable",
        "shipment_ids": [LEDGER_SHIPMENT], "note": "Phải trả cước xe TQ",
    }, "PERF-OBL-1", actor="staging.support")
    assert ok, error

    ok, transaction, error = save_transaction({
        "source_party": {"party_type": "company", "party_id": COMPANY, "name": "Công ty Trường Thành"},
        "holder_party": {"party_type": "agent", "party_id": PARTNER_MASTER, "name": "PHÚ ANH"},
        "amount": 20_000_000, "currency": "VND", "transaction_kind": "payment",
        "shipment_ids": [LEDGER_SHIPMENT], "note": "Chuyển khoản đợt 1",
        "beneficial_owner": {"party_type": "company", "party_id": COMPANY, "name": "Công ty Trường Thành"},
    }, "PERF-TX-1", actor="staging.support")
    assert ok, error

    ok, allocation, error = allocate_transaction(
        transaction["id"], obligation["id"], 20_000_000, "PERF-ALLOC-1",
        currency="VND", shipment_ids=[LEDGER_SHIPMENT], actor="staging.support")
    assert ok, error

    # Same partner, two currencies, on a second shipment → currencies stay apart.
    for index, (currency, amount) in enumerate((("VND", 12_000_000), ("USD", 500)), start=1):
        ok, _row, error = save_obligation({
            "from_party": {"party_type": "company", "party_id": COMPANY, "name": "Công ty Trường Thành"},
            "to_party": {"party_type": "agent", "party_id": PARTNER_UNLISTED, "name": "Đại lý chưa vào master"},
            "amount": amount, "currency": currency, "purpose": "partner_cost_payable",
            "shipment_ids": [PXK_SHIPMENT], "note": f"Phải trả {currency}",
        }, f"PERF-OBL-CCY-{index}", actor="staging.support")
        assert ok, error


def _clone_shipments_to(n: int) -> dict:
    """Clone the seeded shipments up to ``n`` real-schema shipment documents.

    Read-only w.r.t. business semantics: the clones carry the same canonical
    schema as the seed (they are inserted so the reader path sees a
    representative real-database N, exactly like the pilot's ~95 rows).
    """
    db = core_database.get_db()
    template = [dict(doc) for doc in db.shipments.find({}, {"_id": 0})]
    assert template, "the staging seed must provide shipment templates"
    existing = {str(doc.get("id")) for doc in db.shipments.find({}, {"_id": 0, "id": 1})}
    made = 0
    while len(existing) < n:
        source = template[made % len(template)]
        made += 1
        new_id = f"LO-PERF-{made:04d}"
        if new_id in existing:
            continue
        clone = dict(source)
        clone["id"] = new_id
        clone["_id"] = new_id
        db.shipments.insert_one(clone)
        existing.add(new_id)
    return {"ids": sorted(existing)}


@pytest.fixture()
def dataset(staging, event_seq):
    """95 shipments + real ledger rows + a real generated PXK document."""
    _real_pxk_document(event_seq)
    _seed_ledger_records()
    return _clone_shipments_to(N_SHIPMENTS)


# ---------------------------------------------------------------------------
# Read counter — the deterministic acceptance instrument
# ---------------------------------------------------------------------------

class _CountingCollection:
    """Proxy that counts the collection reads (find / find_one) a render makes."""

    def __init__(self, name: str, inner, counts: Counter):
        self._name = name
        self._inner = inner
        self._counts = counts

    def find(self, *args, **kwargs):
        self._counts[self._name] += 1
        return self._inner.find(*args, **kwargs)

    def find_one(self, *args, **kwargs):
        self._counts[self._name] += 1
        return self._inner.find_one(*args, **kwargs)

    def __getattr__(self, item):
        return getattr(self._inner, item)


class _CountingDB:
    def __init__(self, inner, counts: Counter):
        self._inner = inner
        self._counts = counts

    def __getitem__(self, name):
        return _CountingCollection(name, self._inner[name], self._counts)

    def __getattr__(self, item):
        target = getattr(self._inner, item)
        if hasattr(target, "find") and hasattr(target, "count_documents"):
            return _CountingCollection(item, target, self._counts)
        return target


@pytest.fixture()
def read_counter(monkeypatch):
    """Count every Mongo collection read performed through ``core.database``."""
    counts: Counter = Counter()
    original = core_database.get_db
    monkeypatch.setattr(core_database, "get_db", lambda: _CountingDB(original(), counts))
    return counts


@contextmanager
def _no_counting_needed():
    yield


# ---------------------------------------------------------------------------
# The old complexity, reproduced on the SAME fixture (N = 95)
# ---------------------------------------------------------------------------

def test_old_per_shipment_ledger_pattern_is_linear(dataset, read_counter):
    """OLD: ``shipment_partner_position`` per shipment = 3 collection reads each."""
    ids = dataset["ids"]
    assert len(ids) == N_SHIPMENTS

    for sid in ids:
        shipment_partner_position(sid)

    assert read_counter[OBLIGATIONS] == N_SHIPMENTS, (
        "the pre-fix path must be O(N): one full obligations read per shipment"
    )
    assert read_counter[TRANSACTIONS] == N_SHIPMENTS
    assert read_counter[ALLOCATIONS] == N_SHIPMENTS
    # The two global finance worklists ran the same loop again each.
    assert read_counter[OBLIGATIONS] + read_counter[TRANSACTIONS] + read_counter[ALLOCATIONS] == 3 * N_SHIPMENTS


# ---------------------------------------------------------------------------
# A — ledger prefetch: O(1) per render
# ---------------------------------------------------------------------------

def test_render_reads_each_ledger_collection_at_most_once(dataset, read_counter):
    """A: for N=95 the three ledger collections are fetched <= 1 time each."""
    model = vm.build_view_model()
    assert len(model["shipments"]) == N_SHIPMENTS

    assert read_counter[OBLIGATIONS] <= 1, read_counter
    assert read_counter[TRANSACTIONS] <= 1, read_counter
    assert read_counter[ALLOCATIONS] <= 1, read_counter
    assert read_counter[OBLIGATIONS] + read_counter[TRANSACTIONS] + read_counter[ALLOCATIONS] <= 3


def test_ledger_snapshot_is_one_read_and_not_a_cache(dataset, read_counter):
    """The snapshot is request-local: one read, and the next call reads again."""
    first = load_ledger_snapshot()
    assert read_counter[OBLIGATIONS] == 1
    assert read_counter[TRANSACTIONS] == 1
    assert read_counter[ALLOCATIONS] == 1
    assert first["available"] is True

    second = load_ledger_snapshot()
    assert read_counter[OBLIGATIONS] == 2, "a snapshot must never become a stale process cache"
    assert second[OBLIGATIONS] == first[OBLIGATIONS]

    # A fresh snapshot reflects a write that happened after the first read.
    ok, obligation, error = save_obligation({
        "from_party": {"party_type": "company", "party_id": COMPANY, "name": "Công ty Trường Thành"},
        "to_party": {"party_type": "agent", "party_id": PARTNER_MASTER, "name": "PHÚ ANH"},
        "amount": 1_000, "currency": "VND", "purpose": "partner_cost_payable",
        "shipment_ids": [LEDGER_SHIPMENT],
    }, "PERF-OBL-FRESH", actor="staging.support")
    assert ok, error
    fresh = load_ledger_snapshot()
    assert len(fresh[OBLIGATIONS]) == len(first[OBLIGATIONS]) + 1


def test_unknown_stays_unknown_on_the_snapshot_path(dataset):
    """UNKNOWN ≠ ZERO: no ledger record ⇒ None (never 0) and no payable row."""
    with_counter = shipment_partner_position(LEDGER_SHIPMENT, records=load_ledger_snapshot())
    assert with_counter["payable"] == 57_000_000.0

    untouched = next(sid for sid in dataset["ids"] if sid not in {LEDGER_SHIPMENT, PXK_SHIPMENT})
    position = shipment_partner_position(untouched, records=load_ledger_snapshot())
    assert position["status"] == "UNKNOWN"
    assert position["payable"] is None and position["paid"] is None and position["remaining"] is None
    assert position["partners"] == []


# ---------------------------------------------------------------------------
# B — audit timeline: one bounded bulk read
# ---------------------------------------------------------------------------

def test_audit_timeline_is_one_bulk_read_not_one_per_shipment(dataset, read_counter):
    """B: the render's timelines cost ONE audit read; per-shipment costs N."""
    ids = dataset["ids"]

    bulk = rd.timelines_projection(ids)
    assert read_counter["audit_logs"] == 1

    read_counter.clear()
    per_shipment = {sid: rd.timeline_projection(sid) for sid in ids}
    assert read_counter["audit_logs"] == N_SHIPMENTS, (
        "the pre-fix path must be O(N): one audit_logs read per shipment"
    )

    # Same entries, same order, same per-shipment limit semantics.
    assert per_shipment == {sid: bulk.get(sid, []) for sid in ids}
    assert any(per_shipment[sid] for sid in ids), "the fixture must contain real audit history"


def test_render_audit_read_count_is_constant(dataset, read_counter):
    model = vm.build_view_model()
    assert len(model["shipments"]) == N_SHIPMENTS
    assert read_counter["audit_logs"] == 1
    # Every row still carries its own real timeline.
    with_history = [row for row in model["shipments"] if row["timeline"]]
    assert with_history, "the projection must still carry real audit history"


# ---------------------------------------------------------------------------
# C — docgen / PXK: one canonical docgen read
# ---------------------------------------------------------------------------

def test_docgen_read_is_one_per_render_and_pxk_metadata_is_identical(dataset, read_counter):
    """C: canonical docgen metadata is read once; PXK facts are unchanged."""
    db = core_database.get_db()
    assert db["docgen_documents"].count_documents({"shipment_id": PXK_SHIPMENT}) >= 2

    references = vm._load_references()
    shipments = vm.load_shipments()

    # OLD pattern: one docgen read per projected shipment.
    read_counter.clear()
    legacy_pxk = {
        sid: rd.pxk_projection(ship, references["contracts"])
        for sid, ship in shipments.items()
    }
    assert read_counter["docgen_documents"] == len(shipments) == N_SHIPMENTS

    row = legacy_pxk[PXK_SHIPMENT]
    assert row["done"] is True and row["number"] == "PXK-2026-0460"
    assert row["document"]["revision"] == 2, "the latest revision must be selected"

    # NEW pattern: ONE canonical read, shared by every projected shipment.
    read_counter.clear()
    grouped = rd.docgen_documents_by_shipment()
    snapshot_pxk = {
        sid: rd.pxk_projection(ship, references["contracts"], docgen_documents=grouped)
        for sid, ship in shipments.items()
    }
    assert read_counter["docgen_documents"] == 1
    assert snapshot_pxk == legacy_pxk


def test_render_docgen_read_count_is_bounded(dataset, read_counter):
    model = vm.build_view_model()
    assert len(model["shipments"]) == N_SHIPMENTS
    # ONE canonical read for the projected PXK blocks + ONE for C1's own payload.
    assert read_counter["docgen_documents"] <= 2
    row = next(item for item in model["shipments"] if item["id"] == PXK_SHIPMENT)
    assert row["pxk"]["done"] is True and row["pxk"]["number"] == "PXK-2026-0460"


# ---------------------------------------------------------------------------
# D — C1 must not reload the shipments collection
# ---------------------------------------------------------------------------

def test_c1_reuses_the_shipments_loaded_by_the_render(dataset, read_counter):
    """D: supplying the canonical shipment map costs ZERO shipments reads."""
    shipments = vm.load_shipments()
    assert len(shipments) == N_SHIPMENTS

    read_counter.clear()
    supplied = logi_c1.assemble_c1_payload(shipments=shipments)
    assert read_counter["shipments"] == 0, (
        "C1 must not re-fetch the shipments collection the render already loaded"
    )

    read_counter.clear()
    fallback = logi_c1.assemble_c1_payload()
    assert read_counter["shipments"] == 1, "the standalone caller keeps its own read"

    # Supplying the render's map changes nothing in the projection.
    assert supplied == fallback


def test_render_shipment_reads_are_bounded(dataset, read_counter):
    model = vm.build_view_model()
    assert len(model["shipments"]) == N_SHIPMENTS
    # exactly: load_shipments() for the worklist + load_shipment_ids() shared by
    # the two global finance worklists; nothing per shipment.
    assert read_counter["shipments"] <= 2


# ---------------------------------------------------------------------------
# E — output equivalence: fast path vs the unchanged per-call readers
# ---------------------------------------------------------------------------

def test_fast_path_output_equals_legacy_per_call_readers(dataset):
    """E: identical projections — the repair removes reads, not truth."""
    import streamlit as st

    fast = vm.build_view_model()

    # Legacy reconstruction: the SAME projections called per shipment with no
    # snapshot supplied, i.e. the exact reader path that existed before.
    references = vm._load_references()
    shipments = vm.load_shipments()
    views = vm._dashboard_views(shipments)
    # ``companies``/``agents`` are caller-supplied masters, not a snapshot the
    # projection can fall back to reading itself: ``project_commercial_flow``
    # is pure, and BOTH production callers (the build loop and
    # ``vm.read_shipment``) pass ``load_authority_companies()`` explicitly.
    # Omitting them here made the TT_ENTRUSTED_DIRECT row LO-0460 lose its
    # legal importer (name/tax code -> ``ready=False``), which then drifted
    # ``commercialFlow``, the tax-payment step reason and the import tax gate
    # — a reconstruction gap in this test, not fast-path drift. Supply them
    # through the same per-call readers the legacy path used.
    legacy_companies = core_database.load_authority_companies() or {}
    legacy_agents = core_database.load_authority_agents() or {}
    legacy_rows = {
        sid: rd.shipment_projection(
            ship,
            customers=references["customers"],
            contracts=references["contracts"],
            quotes=references["quotes"],
            companies=legacy_companies,
            agents=legacy_agents,
            dashboard=views.get(sid, {}),
            history=rd.timeline_projection(sid),
        )
        for sid, ship in shipments.items()
    }
    fast_rows = {row["id"]: row for row in fast["shipments"]}
    assert set(fast_rows) == set(legacy_rows)
    for sid, row in fast_rows.items():
        assert row == legacy_rows[sid], f"shipment projection drift for {sid}"

    # C2D — global partner payable worklist.
    legacy_payables = rd.partner_payables_projection()
    assert fast["payables"] == legacy_payables
    assert legacy_payables["rows"], "the fixture must produce real payable rows"

    # C2C — customer receivable worklist (derived from the rows above, in the
    # same priority/id order build_view_model sorts them into).
    order = {"Khan": 0, "CanXuLy": 1, "BinhThuong": 2}
    legacy_ordered = sorted(legacy_rows.values(), key=lambda row: (order.get(row["priority"], 9), row["id"]))
    assert fast["receivables"] == rd.receivables_projection(legacy_ordered)

    # /tai-chinh/doi-soat — reconciliation desk over the same ledger.
    legacy_reconciliation = logi_reconciliation.reconciliation_view(
        st.session_state.get(vm.RECONCILIATION_FILTER_KEY),
        known_shipment_ids=list(shipments.keys()),
    )
    assert fast["reconciliation"] == legacy_reconciliation

    # C1 reference payload.
    legacy_c1 = logi_c1.assemble_c1_payload()
    for key in ("contracts", "customers", "quotes", "agreements", "authority"):
        assert fast[key] == legacy_c1[key], f"{key} payload drift"


def test_currency_separation_and_unknown_survive_the_repair(dataset):
    """UNKNOWN ≠ ZERO and currencies are never summed together."""
    model = vm.build_view_model()
    rows = model["payables"]["rows"]

    # The partially paid obligation keeps its exact three figures.
    paid_row = next(r for r in rows if r["shipmentId"] == LEDGER_SHIPMENT and r["partnerId"] == PARTNER_MASTER)
    assert paid_row["currency"] == "VND"
    assert paid_row["payable"] == 57_000_000.0
    assert paid_row["paid"] == 20_000_000.0
    assert paid_row["remaining"] == 37_000_000.0

    # Two currencies, one partner: two rows, no merged figure.
    currencies = {r["currency"] for r in rows if r["shipmentId"] == PXK_SHIPMENT and r["partnerId"] == PARTNER_UNLISTED}
    assert currencies == {"VND", "USD"}
    assert set(model["payables"]["totals"]) == {"VND", "USD"}, "totals stay per currency"
    # 500 USD never becomes part of the VND bucket, and vice versa.
    assert model["payables"]["totals"]["USD"]["payable"] == 500.0
    assert model["payables"]["totals"]["VND"]["payable"] == 57_000_000.0 + 12_000_000.0

    # A shipment with no ledger record contributes no money row at all.
    empty_sid = next(sid for sid in dataset["ids"] if sid not in {LEDGER_SHIPMENT, PXK_SHIPMENT})
    assert not [r for r in rows if r["shipmentId"] == empty_sid]
    partner_block = next(row for row in model["shipments"] if row["id"] == empty_sid)["finance"]["partner"]
    assert partner_block["payable"] is None
    assert partner_block["paid"] is None
    assert partner_block["remaining"] is None
    assert partner_block["status"] == "UNKNOWN"


# ---------------------------------------------------------------------------
# Secondary evidence — LOCAL sandbox timing (never a live-performance claim)
# ---------------------------------------------------------------------------

def test_local_timing_before_after_same_fixture(dataset, capsys):
    """LOCAL timing only: the sandbox has no Atlas network latency.

    The deterministic acceptance evidence is the collection-read count above;
    this measurement is reported as secondary, sandbox-local context.
    """
    references = vm._load_references()
    shipments = vm.load_shipments()
    views = vm._dashboard_views(shipments)

    started = time.perf_counter()
    legacy_rows = [
        rd.shipment_projection(
            ship,
            customers=references["customers"],
            contracts=references["contracts"],
            quotes=references["quotes"],
            dashboard=views.get(sid, {}),
            history=rd.timeline_projection(sid),
        )
        for sid, ship in shipments.items()
    ]
    legacy_payables = rd.partner_payables_projection()
    legacy_ms = (time.perf_counter() - started) * 1000

    started = time.perf_counter()
    fast_model = vm.build_view_model()
    fast_ms = (time.perf_counter() - started) * 1000

    assert len(legacy_rows) == len(fast_model["shipments"]) == N_SHIPMENTS
    assert legacy_payables["rows"], "the fixture must produce real payable rows"
    with capsys.disabled():
        print(f"\n[LOGI_REAL_DATA_RENDER_PERFORMANCE_01] N={N_SHIPMENTS} "
              f"legacy projections+payables={legacy_ms:.1f}ms  build_view_model={fast_ms:.1f}ms "
              f"(LOCAL sandbox timing — Atlas latency not represented)")
