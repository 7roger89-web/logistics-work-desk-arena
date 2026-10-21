"""Bước (3B) — the TWO approved TT_ENTRUSTED_SUB stages.

``entrustment-ready`` and ``tt-warehouse-handover`` exist ONLY for the
sub-entrustment commercial flow.  This module proves the Owner's hard rules:

* the stages never render for CUSTOMER_SELF or TT_ENTRUSTED_DIRECT;
* transport mode (SEA / AIR / ROAD) never adds or removes them;
* a selected legal entity, a LINKED contract, an uploaded file, customs
  clearance, a D/O, a PXK, a selected partner or another leg's DELIVERY are
  NOT completion evidence;
* the handover needs the actual giver/receiver (explicitly recorded), the
  actual time and the handover document number;
* direction is never inferred from the stage name, and the two nodes never
  enter the transport chain (no edges, no CURRENT marker).

All masters and contracts below are explicit FIXTURE records in the isolated
mongomock staging database.  Nothing reads or writes production data.
"""

from __future__ import annotations

import copy

import pytest

from core import database
from core.shipment_journey import (
    ENTRUSTMENT_HANDOVER_ID,
    ENTRUSTMENT_READY_ID,
    JOURNEY_STAGE_IDS,
    build_journey,
)
from core.shipment_document_workflow import (
    ENTRUSTMENT_FIELDS,
    project_entrustment_stages,
    stored_entrustment_evidence,
)
from core.stage_guidance import STAGE_GUIDANCE
from views import logi_sandbox
from views import logi_view_model as vm

SHIPMENT = "LO-0308"
OTHER_SHIPMENT = "LO-0306"

FIXTT = {
    "id": "FIX-TT", "company_id": "FIX-TT",
    "legal_name": "CÔNG TY TNHH TRƯỜNG THÀNH (FIXTURE)",
    "tax_or_legal_code": "0109988776", "is_deleted": False,
}
FIX_IMPORTER_A = {
    "id": "FIX-IMP-A", "company_id": "FIX-IMP-A",
    "legal_name": "CÔNG TY TNHH ĐỐI TÁC NHẬP KHẨU HỘ A (FIXTURE)",
    "tax_or_legal_code": "0317000001", "is_deleted": False,
}
FIX_CONTRACT_B = {
    "id": "FIX-CONTRACT-B", "agent_id": "FIX-CONTRACT-B",
    "legal_name": "CÔNG TY TNHH ĐẠI LÝ HỢP ĐỒNG B (FIXTURE)",
    "legal_code": "0317000002", "is_deleted": False,
}


def _fixture_contract(contract_id: str = "FIX-CONTRACT-199") -> dict:
    """ONE fixture purchase contract matching FIX-TT <-> FIX-CONTRACT-B."""
    return {
        "id": contract_id,
        "contract_no": contract_id,
        "company_id": "FIX-TT",
        "agent_id": "FIX-CONTRACT-B",
        "shipment_ids": [SHIPMENT],
        "status": "active",
        "is_deleted": False,
    }


@pytest.fixture()
def staging():
    import streamlit as st

    logi_sandbox.reset_backend()
    assert logi_sandbox.ensure_backend() == logi_sandbox.SANDBOX_TRANSPORT
    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)
    st.session_state.pop(vm.LAST_WRITES_KEY, None)
    db = database.get_db()
    db["authority_companies"].insert_many([copy.deepcopy(FIXTT), copy.deepcopy(FIX_IMPORTER_A)])
    db["authority_agents"].insert_one(copy.deepcopy(FIX_CONTRACT_B))
    db["contracts"].insert_one(copy.deepcopy(_fixture_contract()))
    yield
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


def _flow_payload(sid: str, request_id: str, **overrides) -> dict:
    payload = {
        "shipmentId": sid,
        "requestId": request_id,
        "mode": "TT_ENTRUSTED_SUB",
        "companyId": "FIX-TT",
        "subAgentId": "FIX-CONTRACT-B",
        "importerCompanyId": "FIX-IMP-A",
    }
    payload.update(overrides)
    return payload


def _confirm_sub(seq_fn, sid: str = SHIPMENT, request_id: str = "FIX-FLOW-199") -> dict:
    outcome = _dispatch(seq_fn, "shipment_commercial_flow_save", _flow_payload(sid, request_id))
    assert outcome["ok"], outcome.get("error")
    return outcome


def _evidence(seq_fn, fields: dict, sid: str = SHIPMENT, request_id: str = "FIX-ENT-199", **extra) -> dict:
    payload = {"shipmentId": sid, "requestId": request_id, "fields": fields}
    payload.update(extra)
    return _dispatch(seq_fn, "entrustment_evidence_save", payload)


def _shipment_row(model: dict, sid: str = SHIPMENT) -> dict:
    return next(row for row in model["shipments"] if row["id"] == sid)


def _node(row: dict, node_id: str) -> dict:
    return next(node for node in row["journey"]["nodes"] if node["id"] == node_id)


def _journey_node(journey: dict, node_id: str) -> dict:
    return next(node for node in journey["nodes"] if node["id"] == node_id)


def _entrustment_rows(model: dict, sid: str = SHIPMENT) -> list[dict]:
    return [
        node for node in _shipment_row(model, sid)["journey"]["nodes"]
        if node["id"] in {ENTRUSTMENT_READY_ID, ENTRUSTMENT_HANDOVER_ID}
    ]


def _ready_fields() -> dict:
    return {
        "entrustment_ready_at": "2026-10-10",
        "entrustment_ready_ref": "HDNT-199/2026 — biên bản phạm vi ủy thác",
    }


def _handover_fields() -> dict:
    return {
        "warehouse_handover_at": "2026-10-12",
        "warehouse_handover_from": "FIX-TT",
        "warehouse_handover_to": "FIX-IMP-A",
        "warehouse_handover_doc_no": "BBGN-199-01",
    }


def _journey_for(flow_mode: str, *, mode: str = "ROAD", contract: dict | None = None) -> dict:
    """Pure build_journey call for the isolation/mode matrix."""
    shipment = {
        "id": "PURE-199",
        "data": {
            "0.0": {"commercial_flow": {
                "mode": flow_mode, "confirmed": True,
                "company_id": "FIX-TT", "sub_agent_id": "FIX-CONTRACT-B",
                "importer_company_id": "FIX-IMP-A" if flow_mode == "TT_ENTRUSTED_SUB" else "",
            }},
            "1.2": {}, "2.4": {}, "2.7": {},
        },
    }
    profile = {
        "mode": mode, "loadModel": "FCL", "serviceScopeConfirmed": True,
        "serviceScope": ["MAIN_CARRIAGE", "IMPORT_CUSTOMS", "DELIVERY"],
        "stages": [
            {"code": "MAIN_CARRIAGE", "label": "Chặng chính", "reason": "SERVICE_SCOPE"},
            {"code": "IMPORT_CUSTOMS", "label": "Hải quan nhập", "reason": "SERVICE_SCOPE"},
            {"code": "DELIVERY", "label": "Giao hàng", "reason": "SERVICE_SCOPE"},
        ],
    }
    entrustment = project_entrustment_stages(
        {"mode": flow_mode, "confirmed": flow_mode == "TT_ENTRUSTED_SUB",
         "ready": flow_mode == "TT_ENTRUSTED_SUB", "missing": [],
         "companyId": "FIX-TT", "companyName": "FIX TT",
         "subAgentId": "FIX-CONTRACT-B", "subAgentName": "FIX B",
         "importerCompanyId": "FIX-IMP-A" if flow_mode == "TT_ENTRUSTED_SUB" else "",
         "legalImporterName": "FIX A"},
        contract or {"status": "LINKED", "id": "FIX-CONTRACT-199", "contractNo": "FIX-CONTRACT-199"},
        {},
    )
    return build_journey(
        shipment, profile=profile, operational={"main_leg": {}, "pickup_leg": {}},
        primary={}, dashboard={}, attachments=[], entrustment_stages=entrustment,
    )


# 1 --------------------------------------------------------------------------
def test_only_sub_flow_renders_the_two_stages():
    for flow in ("CUSTOMER_SELF", "TT_ENTRUSTED_DIRECT"):
        ids = {node["id"] for node in _journey_for(flow)["nodes"]}
        assert ENTRUSTMENT_READY_ID not in ids and ENTRUSTMENT_HANDOVER_ID not in ids, flow
    sub_ids = [node["id"] for node in _journey_for("TT_ENTRUSTED_SUB")["nodes"]]
    assert sub_ids.count(ENTRUSTMENT_READY_ID) == 1
    assert sub_ids.count(ENTRUSTMENT_HANDOVER_ID) == 1


# 2 --------------------------------------------------------------------------
@pytest.mark.parametrize("mode", ["SEA", "AIR", "ROAD"])
def test_transport_mode_never_adds_or_removes_the_sub_stages(mode):
    journey = _journey_for("TT_ENTRUSTED_SUB", mode=mode)
    ids = [node["id"] for node in journey["nodes"]]
    assert ids.count(ENTRUSTMENT_READY_ID) == 1
    assert ids.count(ENTRUSTMENT_HANDOVER_ID) == 1
    # They are NOT inside the transport chain: no edge, no dependency, and the
    # CURRENT marker never moves onto them.
    assert all(edge["to"] not in {ENTRUSTMENT_READY_ID, ENTRUSTMENT_HANDOVER_ID} for edge in journey["edges"])
    assert all(edge["from"] not in {ENTRUSTMENT_READY_ID, ENTRUSTMENT_HANDOVER_ID} for edge in journey["edges"])
    assert journey["currentStageId"] not in {ENTRUSTMENT_READY_ID, ENTRUSTMENT_HANDOVER_ID}
    for node_id in (ENTRUSTMENT_READY_ID, ENTRUSTMENT_HANDOVER_ID):
        assert _journey_node(journey, node_id)["dependencies"] == []


# 3 --------------------------------------------------------------------------
def test_linked_contract_legal_entity_file_customs_pxk_and_delivery_are_not_done(staging, event_seq):
    _confirm_sub(event_seq)
    db = database.get_db()
    document = db["shipments"].find_one({"id": SHIPMENT})
    assert document is not None
    data = document.setdefault("data", {})
    # Every "plausible but wrong" signal at once.
    data.setdefault("2.4", {})["customs_status"] = True
    data.setdefault("2.4", {})["clearance_date"] = "2026-10-11"
    data.setdefault("2.7", {})["is_delivered"] = True
    data.setdefault("2.7", {})["delivered_at"] = "2026-10-13"
    data.setdefault("1.2", {})["sea_export"] = {"do_released_at": "2026-10-11", "pod_received_at": "2026-10-13"}
    db["shipments"].replace_one({"id": SHIPMENT}, document)
    db["shipment_attachments"].insert_one({
        "id": "ATT-FIX-199", "shipment_id": SHIPMENT, "name": "BBGN.pdf",
        "category": "customs", "is_deleted": False,
    })

    row = _shipment_row(vm.build_view_model())
    assert row["documentWorkflow"]  # projection still builds
    for node_id in (ENTRUSTMENT_READY_ID, ENTRUSTMENT_HANDOVER_ID):
        node = _node(row, node_id)
        assert node["completed"] is False, node_id
        assert node["state"] != "COMPLETED", node_id
        assert node["missingEvidence"], node_id


# 4 --------------------------------------------------------------------------
def test_support_records_ready_evidence_and_reads_it_back(staging, event_seq):
    _confirm_sub(event_seq)
    assert _shipment_row(vm.build_view_model())["entrustmentStages"]["ready"]["done"] is False

    outcome = _evidence(event_seq, _ready_fields())
    assert outcome["ok"], outcome.get("error")
    assert outcome["persisted"]["entrustmentEvidence"]["ready_at"] == "2026-10-10"
    readback = outcome["readback"]["entrustmentStages"]
    assert readback["ready"]["done"] is True
    assert readback["handover"]["done"] is False

    row = _shipment_row(vm.build_view_model())
    ready = _node(row, ENTRUSTMENT_READY_ID)
    assert ready["completed"] is True
    assert ready["factValues"]["entrustment_ready_ref"].startswith("HDNT-199")
    assert _node(row, ENTRUSTMENT_HANDOVER_ID)["completed"] is False


# 5 --------------------------------------------------------------------------
def test_ready_cannot_be_recorded_without_a_linked_contract(staging, event_seq):
    _confirm_sub(event_seq)
    database.get_db()["contracts"].update_one(
        {"id": "FIX-CONTRACT-199"}, {"$set": {"company_id": "FIX-OTHER"}}
    )
    before = vm.read_shipment(SHIPMENT)
    outcome = _evidence(event_seq, _ready_fields())
    assert outcome["ok"] is False
    assert outcome["gate"] == "ENTRUSTMENT_EVIDENCE_REFUSED"
    assert "hợp đồng liên kết" in outcome["error"].lower()
    after = vm.read_shipment(SHIPMENT)
    assert int(after.get("version") or 0) == int(before.get("version") or 0)
    assert stored_entrustment_evidence(after)["ready_at"] == ""


# 6 --------------------------------------------------------------------------
@pytest.mark.parametrize("fields, reason", [
    ({"warehouse_handover_at": "2026-10-12"}, "đủ thời điểm"),
    ({**_handover_fields(), "warehouse_handover_from": ""}, "đủ thời điểm"),
    ({**_handover_fields(), "warehouse_handover_to": "FIX-TT"}, "phải khác nhau"),
    ({**_handover_fields(), "warehouse_handover_to": "FIX-UNKNOWN"}, "thuộc chuỗi ủy thác"),
    ({**_handover_fields(), "warehouse_handover_doc_no": ""}, "đủ thời điểm"),
])
def test_handover_requires_both_actual_parties_time_and_document(staging, event_seq, fields, reason):
    _confirm_sub(event_seq)
    assert _evidence(event_seq, _ready_fields())["ok"]
    outcome = _evidence(event_seq, fields)
    assert outcome["ok"] is False
    assert outcome["gate"] == "ENTRUSTMENT_EVIDENCE_REFUSED"
    assert reason in outcome["error"]
    assert stored_entrustment_evidence(vm.read_shipment(SHIPMENT))["handover_at"] == ""


# 7 --------------------------------------------------------------------------
def test_handover_completes_only_with_recorded_giver_receiver_and_minutes(staging, event_seq):
    _confirm_sub(event_seq)
    assert _evidence(event_seq, _ready_fields())["ok"]
    outcome = _evidence(event_seq, _handover_fields())
    assert outcome["ok"], outcome.get("error")
    stages = outcome["readback"]["entrustmentStages"]
    assert stages["handover"]["done"] is True
    assert FIXTT["legal_name"] in stages["handover"]["evidence"]
    assert FIX_IMPORTER_A["legal_name"] in stages["handover"]["evidence"]
    assert "BBGN-199-01" in stages["handover"]["evidence"]

    node = _node(_shipment_row(vm.build_view_model()), ENTRUSTMENT_HANDOVER_ID)
    assert node["completed"] is True
    assert node["factValues"]["warehouse_handover_from"] == "FIX-TT"
    assert node["factValues"]["warehouse_handover_to"] == "FIX-IMP-A"


# 8 --------------------------------------------------------------------------
def test_direction_is_recorded_never_inferred_from_the_stage_name(staging, event_seq):
    _confirm_sub(event_seq)
    assert _evidence(event_seq, _ready_fields())["ok"]
    # The panel offers the three chain parties as explicit choices; a blank
    # choice is an explicit UNKNOWN, not a default.
    node = _node(_shipment_row(vm.build_view_model()), ENTRUSTMENT_HANDOVER_ID)
    from_field = next(f for f in node["factFields"] if f["key"] == "warehouse_handover_from")
    to_field = next(f for f in node["factFields"] if f["key"] == "warehouse_handover_to")
    assert {o["value"] for o in from_field["options"]} == {"FIX-TT", "FIX-CONTRACT-B", "FIX-IMP-A"}
    assert {o["value"] for o in to_field["options"]} == {"FIX-TT", "FIX-CONTRACT-B", "FIX-IMP-A"}
    assert node["factValues"]["warehouse_handover_from"] == ""
    assert node["factValues"]["warehouse_handover_to"] == ""
    # Recording the reverse direction is accepted exactly as recorded.
    reversed_fields = {**_handover_fields(), "warehouse_handover_from": "FIX-IMP-A", "warehouse_handover_to": "FIX-TT"}
    outcome = _evidence(event_seq, reversed_fields)
    assert outcome["ok"], outcome.get("error")
    evidence = outcome["readback"]["entrustmentStages"]["handover"]["evidence"]
    assert evidence.index(FIX_IMPORTER_A["legal_name"]) < evidence.index(FIXTT["legal_name"])


# 9 --------------------------------------------------------------------------
def test_only_authorized_roles_and_only_the_sub_flow_can_write(staging, event_seq):
    import streamlit as st

    _confirm_sub(event_seq)
    for role in ("accounting", "operations", "viewer"):
        st.session_state["current_user"] = {
            "username": f"{role}-fixture", "role": role, "name": role,
        }
        refused = _evidence(event_seq, _ready_fields())
        assert refused["ok"] is False, role
        assert refused["error"].startswith("RBAC:"), role

    st.session_state["current_user"] = {
        "username": "sale-fixture", "role": "sale", "name": "sale",
    }
    assert _evidence(event_seq, _ready_fields())["ok"]

    # A non-SUB lot is refused even for an authorized actor.
    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)
    direct = _dispatch(event_seq, "shipment_commercial_flow_save", _flow_payload(
        OTHER_SHIPMENT, "FIX-FLOW-DIRECT-199", mode="TT_ENTRUSTED_DIRECT",
        importerCompanyId="", subAgentId="",
    ))
    assert direct["ok"], direct.get("error")
    refused = _evidence(event_seq, _ready_fields(), sid=OTHER_SHIPMENT, request_id="FIX-ENT-DIRECT")
    assert refused["ok"] is False
    assert "chỉ áp dụng cho luồng ủy thác tiếp" in refused["error"]


# 10 -------------------------------------------------------------------------
def test_time_inversion_stale_version_and_blanking_are_refused(staging, event_seq):
    _confirm_sub(event_seq)
    assert _evidence(event_seq, _ready_fields())["ok"]

    inverted = _evidence(event_seq, {**_handover_fields(), "warehouse_handover_at": "2026-10-09"})
    assert inverted["ok"] is False
    assert "trước ngày xác nhận" in inverted["error"]

    stale = _evidence(event_seq, _handover_fields(), expectedVersion=999)
    assert stale["ok"] is False
    assert stale["gate"] == "STALE_VERSION"

    clearing = _evidence(event_seq, {"entrustment_ready_ref": ""})
    assert clearing["ok"] is False
    assert "Không được xóa" in clearing["error"]

    unknown_key = _evidence(event_seq, {"customs_cleared": "true"})
    assert unknown_key["ok"] is False
    assert "không thuộc bằng chứng" in unknown_key["error"]


# regressions ----------------------------------------------------------------
def test_both_ids_are_registered_real_stages_with_bounded_popups():
    assert ENTRUSTMENT_READY_ID in JOURNEY_STAGE_IDS
    assert ENTRUSTMENT_HANDOVER_ID in JOURNEY_STAGE_IDS
    for node_id in (ENTRUSTMENT_READY_ID, ENTRUSTMENT_HANDOVER_ID):
        row = STAGE_GUIDANCE[node_id]
        assert set(row) == {"why", "what_to_do", "who", "when", "needs", "done_when", "impact"}
        assert all(len(value) <= 120 for value in row.values()), node_id
    node = _journey_node(_journey_for("TT_ENTRUSTED_SUB"), ENTRUSTMENT_HANDOVER_ID)
    assert len([field for field in node["factFields"] if not field.get("secondary")]) <= 5
    assert set(node["guidance"]) == {"why", "what_to_do", "who", "when", "needs", "done_when", "impact"}


def test_existing_transport_nodes_keep_their_completion_and_edges():
    sub = _journey_for("TT_ENTRUSTED_SUB", mode="SEA")
    other = _journey_for("CUSTOMER_SELF", mode="SEA")
    sub_base = [node for node in sub["nodes"] if node["id"] not in {ENTRUSTMENT_READY_ID, ENTRUSTMENT_HANDOVER_ID}]
    assert [node["id"] for node in sub_base] == [node["id"] for node in other["nodes"]]
    assert sub["edges"] == other["edges"]
    assert sub["currentStageId"] == other["currentStageId"]
    for left, right in zip(sub_base, other["nodes"]):
        assert left["completed"] is right["completed"]
        assert left["state"] == right["state"]


def test_evidence_field_map_is_bounded_and_matches_the_stored_keys():
    # LOGI-211-HANDOVER-LABEL-MST (Owner D2): the bounded map deliberately
    # gains exactly the 2 stage-local display-name fields — nothing else.
    assert set(ENTRUSTMENT_FIELDS) == {
        "entrustment_ready_at", "entrustment_ready_ref",
        "warehouse_handover_at", "warehouse_handover_from",
        "warehouse_handover_from_label",
        "warehouse_handover_to", "warehouse_handover_to_label",
        "warehouse_handover_doc_no",
    }


# DOM lane ------------------------------------------------------------------
def test_runtime_dom_renders_the_two_stages_and_their_evidence_panel(staging, event_seq):
    """Deterministic jsdom render of the committed bundle (no browser claim)."""
    import json
    import os
    import shutil
    import subprocess
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent
    node = shutil.which("node")
    if not node or not (root / "component/node_modules/jsdom").exists():
        pytest.skip("node + component/node_modules/jsdom required for the DOM lane")

    _confirm_sub(event_seq)
    assert _evidence(event_seq, _ready_fields())["ok"]
    row = _shipment_row(vm.build_view_model())
    sub_nodes = row["journey"]["nodes"]
    without = [
        node_row for node_row in sub_nodes
        if node_row["id"] not in {ENTRUSTMENT_READY_ID, ENTRUSTMENT_HANDOVER_ID}
    ]
    payload = {"sub": sub_nodes, "self": without}

    script = """
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import { pathToFileURL } from "node:url";
import path from "node:path";
const root = process.cwd();
const require = createRequire(path.join(root, "component/package.json"));
const { JSDOM } = require("jsdom");
const payload = JSON.parse(process.env.NODES_JSON);
const base = JSON.parse(readFileSync("tests/component/fixtures/view_model_journey_fresh_188.json", "utf8")).before;
const dom = new JSDOM("<!doctype html><body><div id=\\"host\\"></div>", { url: "http://localhost:9503", pretendToBeVisual: true });
globalThis.window = dom.window; globalThis.document = dom.window.document;
Object.defineProperty(globalThis, "navigator", { value: dom.window.navigator, configurable: true });
for (const k of ["HTMLElement", "HTMLInputElement", "HTMLSelectElement", "HTMLTextAreaElement", "Event", "MouseEvent", "Node", "MutationObserver", "getComputedStyle"]) globalThis[k] = dom.window[k];
dom.window.HTMLElement.prototype.scrollIntoView = function () {};
const mount = (await import(pathToFileURL(path.resolve("component/dist/logi-shell.js")))).default;
const tick = (ms = 120) => new Promise((r) => setTimeout(r, ms));
const waitFor = async (fn, ms = 5000) => {
  const end = Date.now() + ms;
  while (Date.now() < end) { const v = fn(); if (v) return v; await tick(50); }
  return fn();
};
const click = async (el) => { el.dispatchEvent(new MouseEvent("click", { bubbles: true, cancelable: true })); await tick(); };
const text = (el) => el.textContent.replace(/\\s+/g, " ").trim();
const byId = (id) => document.querySelector(`[data-testid="${id}"]`);

const openShipment = async () => {
  await click([...document.querySelectorAll("a")].find(a => text(a) === "Lô Hàng"));
  await click(await waitFor(() => byId("shipment-period-tat-ca")));
  await click(await waitFor(() => [...document.querySelectorAll("main a")].find(a => text(a) === "LO-0308")));
  await waitFor(() => byId("journey-node-customs-import"));
};

const subVm = structuredClone(base);
const subRow = subVm.shipments.find(s => s.id === "LO-0308");
subRow.journey.nodes = payload.sub;
mount({ name: "logi_shell", data: subVm, parentElement: document.getElementById("host"), setTriggerValue: () => {} });
await tick(250);
await openShipment();
const ready = await waitFor(() => byId("journey-node-entrustment-ready"));
const handover = await waitFor(() => byId("journey-node-tt-warehouse-handover"));
const readyText = text(ready);
const handoverText = text(handover);
// The READY node is already proven by the recorded evidence; its own panel
// must render without inventing extra fields.
await click(ready);
let bubble = await waitFor(() => byId("journey-bubble"));
const readyBubbleText = [...bubble.querySelectorAll("*")].map(text).join(" | ");
await click(bubble.querySelector("button[data-testid^=\\"journey-bubble-task-\\"]"));
const readyPanel = await waitFor(() => byId("entrustment-evidence"));
const readyLabels = [...readyPanel.querySelectorAll("select, input")].map(e => e.getAttribute("aria-label")).filter(Boolean);
const readyMissing = byId("entrustment-missing") ? text(byId("entrustment-missing")) : "";
// Re-mount and open the HANDOVER node: incomplete by design, so it must list
// exactly what is missing and expose the bounded fields (4 primary handover
// fields + 2 folded secondary display-name fields, LOGI-211 D2).
mount({ name: "logi_shell", data: subVm, parentElement: document.getElementById("host"), setTriggerValue: () => {} });
await tick(250);
await openShipment();
await click(await waitFor(() => byId("journey-node-tt-warehouse-handover")));
bubble = await waitFor(() => byId("journey-bubble"));
const handoverBubbleText = [...bubble.querySelectorAll("*")].map(text).join(" | ");
await click(bubble.querySelector("button[data-testid^=\\"journey-bubble-task-\\"]"));
const panel = await waitFor(() => byId("entrustment-evidence"));
const fieldLabels = [...panel.querySelectorAll("select, input")].map(e => e.getAttribute("aria-label")).filter(Boolean);
panel.querySelector("button[data-testid=\\"entrustment-evidence-save\\"]");
const missing = byId("entrustment-missing") ? text(byId("entrustment-missing")) : "";

const selfVm = structuredClone(base);
selfVm.shipments.find(s => s.id === "LO-0308").journey.nodes = payload.self;
mount({ name: "logi_shell", data: selfVm, parentElement: document.getElementById("host"), setTriggerValue: () => {} });
await tick(250);
await waitFor(() => byId("journey-node-customs-import"));
const selfReady = byId("journey-node-entrustment-ready");
const selfHandover = byId("journey-node-tt-warehouse-handover");
console.log(JSON.stringify({
  readyText, handoverText, readyBubbleText, handoverBubbleText,
  readyLabels, readyMissing, fieldLabels, missing,
  selfReady: Boolean(selfReady), selfHandover: Boolean(selfHandover),
}));
"""
    result = subprocess.run(
        [node, "--input-type=module", "-e", script],
        cwd=str(root),
        env=dict(os.environ, NODES_JSON=json.dumps(payload, ensure_ascii=False)),
        capture_output=True, text=True, check=True, timeout=90,
    )
    out = json.loads(result.stdout.strip().splitlines()[-1])
    assert "ĐỦ ĐIỀU KIỆN" in out["readyText"].upper()
    assert "BÀN GIAO" in out["handoverText"].upper()
    assert "ĐỦ ĐIỀU KIỆN THỰC HIỆN" in out["readyBubbleText"].upper()
    assert "BÀN GIAO HÀNG TẠI KHO" in out["handoverBubbleText"].upper()
    assert out["readyLabels"] == ["Ngày xác nhận đủ điều kiện thực hiện", "Căn cứ xác nhận (số hợp đồng / biên bản phạm vi ủy thác)"]
    assert out["readyMissing"] == ""
    # LOGI-211-HANDOVER-LABEL-MST (Owner D2): +2 secondary display-name
    # fields, rendered folded after the 4 primary handover fields.
    assert out["fieldLabels"] == [
        "Thời điểm bàn giao thực tế", "Bên giao (ghi nhận thực tế)",
        "Bên nhận (ghi nhận thực tế)", "Số biên bản giao nhận",
        "Tên hiển thị bên giao (nếu tên danh mục chưa đúng)",
        "Tên hiển thị bên nhận (nếu tên danh mục chưa đúng)",
    ]
    assert "Còn thiếu để xác nhận" in out["missing"]
    assert "bàn giao" in out["missing"].lower()
    assert out["selfReady"] is False and out["selfHandover"] is False


# P0-A — a stored handover can never outrun its prerequisite ------------------
def test_p0a_writer_refuses_full_handover_without_ready_evidence(staging, event_seq):
    """TASK 2.1 — no ready_at/ready_ref: the four handover fields are refused."""
    _confirm_sub(event_seq)
    before = vm.read_shipment(SHIPMENT)
    version_before = int(before.get("version") or 0)

    outcome = _evidence(event_seq, _handover_fields(), request_id="FIX-ENT-P0A-1")
    assert outcome["ok"] is False
    assert outcome["gate"] == "ENTRUSTMENT_EVIDENCE_REFUSED"
    assert "ủy thác sẵn sàng" in outcome["error"]

    after = vm.read_shipment(SHIPMENT)
    assert int(after.get("version") or 0) == version_before
    assert stored_entrustment_evidence(after) == {
        "ready_at": "", "ready_ref": "",
        "handover_at": "", "handover_from": "", "handover_from_label": "",
        "handover_to": "", "handover_to_label": "", "handover_doc_no": "",
    }


def test_p0a_projection_handover_not_done_without_ready_evidence():
    """TASK 2.2 — legacy/planted evidence: projection fails closed, keeps data."""
    evidence = {**{ENTRUSTMENT_FIELDS["warehouse_handover_at"]: "2026-10-12",
                   ENTRUSTMENT_FIELDS["warehouse_handover_from"]: "FIX-TT",
                   ENTRUSTMENT_FIELDS["warehouse_handover_to"]: "FIX-IMP-A",
                   ENTRUSTMENT_FIELDS["warehouse_handover_doc_no"]: "BBGN-199-01"}}
    flow = {
        "mode": "TT_ENTRUSTED_SUB", "confirmed": True, "ready": True, "missing": [],
        "companyId": "FIX-TT", "companyName": "FIX TT",
        "subAgentId": "FIX-CONTRACT-B", "subAgentName": "FIX B",
        "importerCompanyId": "FIX-IMP-A", "legalImporterName": "FIX A",
    }
    stages = project_entrustment_stages(
        flow, {"status": "LINKED", "id": "FIX-CONTRACT-199", "contractNo": "FIX-CONTRACT-199"}, evidence,
    )
    assert stages["ready"]["done"] is False
    assert stages["handover"]["done"] is False
    assert any("ủy thác sẵn sàng" in item for item in stages["handover"]["missing"])
    # The recorded evidence is preserved and still readable.
    assert stages["values"]["warehouse_handover_doc_no"] == "BBGN-199-01"


def test_p0a_lost_legal_importer_fails_closed_and_keeps_history(staging, event_seq):
    """TASK 2.3 — importer removed from the master after a valid save."""
    _confirm_sub(event_seq)
    assert _evidence(event_seq, _ready_fields(), request_id="FIX-P0A-READY")["ok"]
    assert _evidence(event_seq, _handover_fields(), request_id="FIX-P0A-HAND")["ok"]
    assert _node(_shipment_row(vm.build_view_model()), ENTRUSTMENT_HANDOVER_ID)["completed"] is True

    database.get_db()["authority_companies"].delete_one({"company_id": "FIX-IMP-A"})
    row = _shipment_row(vm.build_view_model())
    stages = row["entrustmentStages"]
    assert stages["ready"]["done"] is False
    assert stages["handover"]["done"] is False
    assert any("pháp nhân" in item for item in stages["ready"]["missing"])
    assert any("ủy thác sẵn sàng" in item for item in stages["handover"]["missing"])

    handover = _node(row, ENTRUSTMENT_HANDOVER_ID)
    assert handover["completed"] is False
    assert handover["state"] != "COMPLETED"
    # Historical evidence survives: the read-back panel still shows what was recorded.
    assert handover["factValues"]["warehouse_handover_doc_no"] == "BBGN-199-01"
    assert stored_entrustment_evidence(vm.read_shipment(SHIPMENT))["handover_at"] == "2026-10-12"


def test_p0a_contract_leaving_linked_or_becoming_ambiguous_fails_closed(staging, event_seq):
    """TASK 2.4 — completion fails closed when the contract stops being LINKED."""
    db = database.get_db()
    _confirm_sub(event_seq)
    assert _evidence(event_seq, _ready_fields(), request_id="FIX-P0A-R2")["ok"]
    assert _evidence(event_seq, _handover_fields(), request_id="FIX-P0A-H2")["ok"]

    # (a) the contract no longer matches the two parties -> MISSING
    db["contracts"].update_one({"id": "FIX-CONTRACT-199"}, {"$set": {"agent_id": "FIX-OTHER"}})
    stages = _shipment_row(vm.build_view_model())["entrustmentStages"]
    assert stages["ready"]["done"] is False
    assert stages["handover"]["done"] is False
    assert any("hợp đồng liên kết" in item for item in stages["ready"]["missing"])

    # (b) two contracts match the same pair -> AMBIGUOUS (never auto-picked)
    db["contracts"].update_one({"id": "FIX-CONTRACT-199"}, {"$set": {"agent_id": "FIX-CONTRACT-B"}})
    db["contracts"].insert_one(copy.deepcopy({
        **_fixture_contract("FIX-CONTRACT-199-B"),
    }))
    row = _shipment_row(vm.build_view_model())
    stages = row["entrustmentStages"]
    assert stages["ready"]["done"] is False
    assert stages["handover"]["done"] is False
    assert any("cùng khớp hai bên" in item for item in stages["ready"]["missing"])
    assert _node(row, ENTRUSTMENT_HANDOVER_ID)["completed"] is False
    assert stored_entrustment_evidence(vm.read_shipment(SHIPMENT))["ready_ref"].startswith("HDNT-199")


# P0-B — timestamps keep their hours/minutes and are validated as a whole ------
def test_p0b_same_day_earlier_time_is_refused(staging, event_seq):
    """TASK 2.5 — 18:00 ready, 09:00 handover, same day: REFUSED."""
    _confirm_sub(event_seq)
    assert _evidence(event_seq, {**_ready_fields(), "entrustment_ready_at": "2026-10-10T18:00"},
                     request_id="FIX-P0B-R1")["ok"]
    before = vm.read_shipment(SHIPMENT)
    outcome = _evidence(event_seq, {**_handover_fields(), "warehouse_handover_at": "2026-10-10T09:00"},
                        request_id="FIX-P0B-H1")
    assert outcome["ok"] is False
    assert outcome["gate"] == "ENTRUSTMENT_EVIDENCE_REFUSED"
    assert "trước giờ xác nhận" in outcome["error"]
    after = vm.read_shipment(SHIPMENT)
    assert int(after.get("version") or 0) == int(before.get("version") or 0)
    assert stored_entrustment_evidence(after)["handover_at"] == ""


def test_p0b_later_time_is_accepted_and_readback_keeps_hhmm(staging, event_seq):
    """TASK 2.6 — 18:00 ready, 19:00 handover: ACCEPTED, HH:mm preserved."""
    _confirm_sub(event_seq)
    assert _evidence(event_seq, {**_ready_fields(), "entrustment_ready_at": "2026-10-10T18:00"},
                     request_id="FIX-P0B-R2")["ok"]
    outcome = _evidence(event_seq, {**_handover_fields(), "warehouse_handover_at": "2026-10-10T19:00"},
                        request_id="FIX-P0B-H2")
    assert outcome["ok"], outcome.get("error")
    persisted = outcome["persisted"]["entrustmentEvidence"]
    assert persisted["ready_at"] == "2026-10-10T18:00"
    assert persisted["handover_at"] == "2026-10-10T19:00"
    stages = outcome["readback"]["entrustmentStages"]
    assert stages["ready"]["done"] is True and stages["handover"]["done"] is True
    assert "18:00" in stages["ready"]["evidence"] and "19:00" in stages["handover"]["evidence"]

    node = _node(_shipment_row(vm.build_view_model()), ENTRUSTMENT_HANDOVER_ID)
    assert node["factValues"]["warehouse_handover_at"] == "2026-10-10T19:00"


def test_p0b_trailing_garbage_is_refused_not_truncated(staging, event_seq):
    """TASK 2.7 — '2026-10-10NOT-A-TIME' must not pass as a date."""
    _confirm_sub(event_seq)
    before = vm.read_shipment(SHIPMENT)
    outcome = _evidence(event_seq, {**_ready_fields(), "entrustment_ready_at": "2026-10-10NOT-A-TIME"},
                        request_id="FIX-P0B-G1")
    assert outcome["ok"] is False
    assert "Mốc thời gian" in outcome["error"]
    after = vm.read_shipment(SHIPMENT)
    assert int(after.get("version") or 0) == int(before.get("version") or 0)
    assert stored_entrustment_evidence(after)["ready_at"] == ""


def test_p0b_date_only_legacy_contract_is_explicit_and_invents_no_hour(staging, event_seq):
    """TASK 2.8 (superseded assertion) — pure dates stay pure.

    UPDATED 2026-10-19: this test used to accept a same-day MIXED-precision
    handover (ready date-only, handover date+time). That assertion pinned the
    cross-precision false-DONE found by Control Tower, so it is now inverted:
    the order is unprovable and the write is refused. The date-only/date-only
    legacy contract is kept exactly as before (asserted here and below).
    """
    from core.shipment_document_workflow import _normalize_evidence_time

    _confirm_sub(event_seq)
    assert _normalize_evidence_time("2026-10-10") == "2026-10-10"
    assert _normalize_evidence_time("10/10/2026") == "2026-10-10"

    # Same-day mixed precision: order NOT provable -> refused, nothing stored.
    assert _evidence(event_seq, _ready_fields(), request_id="FIX-P0B-D1")["ok"]
    before = vm.read_shipment(SHIPMENT)
    mixed = _evidence(event_seq, {**_handover_fields(), "warehouse_handover_at": "2026-10-10T09:00"},
                      request_id="FIX-P0B-D2")
    assert mixed["ok"] is False
    assert mixed["gate"] == "ENTRUSTMENT_EVIDENCE_REFUSED"
    assert "chưa chứng minh được" in mixed["error"]
    assert int(vm.read_shipment(SHIPMENT).get("version") or 0) == int(before.get("version") or 0)

    # Same precision keeps exact ordering: a pure date before the ready date fails.
    fresh = _evidence(event_seq, {**_handover_fields(), "warehouse_handover_at": "2026-10-09"},
                      request_id="FIX-P0B-D3")
    assert fresh["ok"] is False
    assert "trước ngày xác nhận" in fresh["error"]


def test_p0a_linked_never_becomes_signed_or_effective_evidence(staging, event_seq):
    """LINKED is a precondition only — recording ready never upgrades the contract."""
    db = database.get_db()
    _confirm_sub(event_seq)
    contract_before = copy.deepcopy(db["contracts"].find_one({"id": "FIX-CONTRACT-199"}, {"_id": 0}))

    # LINKED alone (no ready facts) is not completion.
    row = _shipment_row(vm.build_view_model())
    assert _node(row, ENTRUSTMENT_READY_ID)["completed"] is False
    assert row["entrustmentStages"]["contractNo"] == "FIX-CONTRACT-199"

    assert _evidence(event_seq, _ready_fields(), request_id="FIX-P0A-LINKED")["ok"]
    contract_after = db["contracts"].find_one({"id": "FIX-CONTRACT-199"}, {"_id": 0})
    assert copy.deepcopy(contract_after) == contract_before
    assert contract_after["status"] == "active"
    stages = _shipment_row(vm.build_view_model())["entrustmentStages"]
    assert stages["ready"]["done"] is True
    assert stages["handover"]["done"] is False
    # The rendered evidence still names the contract; no fabricated signature claim.
    assert "FIX-CONTRACT-199" in stages["ready"]["evidence"]
    assert not any(word in stages["ready"]["evidence"].lower() for word in ("đã ký", "hiệu lực", "signed", "effective"))


def test_p0b_garbage_already_stored_cannot_complete_the_handover(staging, event_seq):
    """A legacy row written before the parser fix must not stay DONE."""
    _confirm_sub(event_seq)
    db = database.get_db()
    document = db["shipments"].find_one({"id": SHIPMENT})
    document["data"]["0.0"]["entrustment_evidence"] = {
        "ready_at": "2026-10-10", "ready_ref": "HDNT-199/2026",
        "handover_at": "2026-10-10NOT-A-TIME", "handover_from": "FIX-TT",
        "handover_to": "FIX-IMP-A", "handover_doc_no": "BBGN-199-01",
    }
    db["shipments"].replace_one({"id": SHIPMENT}, document)

    row = _shipment_row(vm.build_view_model())
    stages = row["entrustmentStages"]
    assert stages["ready"]["done"] is True
    assert stages["handover"]["done"] is False
    assert any("không đúng định dạng" in item for item in stages["handover"]["missing"])
    assert _node(row, ENTRUSTMENT_HANDOVER_ID)["completed"] is False
    # The operator can repair it with a valid value through the same writer.
    fixed = _evidence(event_seq, {"warehouse_handover_at": "2026-10-12"},
                      request_id="FIX-P0B-REPAIR")
    assert fixed["ok"], fixed.get("error")
    assert _node(_shipment_row(vm.build_view_model()), ENTRUSTMENT_HANDOVER_ID)["completed"] is True


# Cross-precision ordering — the DAY is always determinate -------------------
def test_cross_precision_day_inversion_is_refused_regardless_of_hours(staging, event_seq):
    """TASK 2 (a,b) — a handover dated before the ready day always fails."""
    _confirm_sub(event_seq)
    # (a) ready date-only, handover previous day WITH a time
    assert _evidence(event_seq, _ready_fields(), request_id="FIX-XP-R1")["ok"]
    before = vm.read_shipment(SHIPMENT)
    earlier_with_time = _evidence(
        event_seq, {**_handover_fields(), "warehouse_handover_at": "2026-10-09T09:00"},
        request_id="FIX-XP-H1",
    )
    assert earlier_with_time["ok"] is False
    assert earlier_with_time["gate"] == "ENTRUSTMENT_EVIDENCE_REFUSED"
    assert "trước ngày xác nhận" in earlier_with_time["error"]
    assert int(vm.read_shipment(SHIPMENT).get("version") or 0) == int(before.get("version") or 0)
    assert stored_entrustment_evidence(vm.read_shipment(SHIPMENT))["handover_at"] == ""


def test_cross_precision_ready_datetime_vs_handover_day_before_is_refused(staging, event_seq):
    """TASK 2 (b) — ready with 18:00, handover the PREVIOUS day (date-only)."""
    _confirm_sub(event_seq)
    assert _evidence(event_seq, {**_ready_fields(), "entrustment_ready_at": "2026-10-10T18:00"},
                     request_id="FIX-XP-R2")["ok"]
    outcome = _evidence(event_seq, {**_handover_fields(), "warehouse_handover_at": "2026-10-09"},
                        request_id="FIX-XP-H2")
    assert outcome["ok"] is False
    assert "trước ngày xác nhận" in outcome["error"]
    assert stored_entrustment_evidence(vm.read_shipment(SHIPMENT))["handover_at"] == ""


def test_cross_precision_later_day_is_accepted_without_reading_clocks(staging, event_seq):
    """TASK 2 (c) — a later DAY is ordered, so mixed precision is harmless."""
    _confirm_sub(event_seq)
    assert _evidence(event_seq, _ready_fields(), request_id="FIX-XP-R3")["ok"]
    outcome = _evidence(event_seq, {**_handover_fields(), "warehouse_handover_at": "2026-10-11T09:00"},
                        request_id="FIX-XP-H3")
    assert outcome["ok"], outcome.get("error")
    stages = outcome["readback"]["entrustmentStages"]
    assert stages["handover"]["done"] is True
    assert outcome["persisted"]["entrustmentEvidence"]["handover_at"] == "2026-10-11T09:00"


@pytest.mark.parametrize("ready,handover,label", [
    ("2026-10-10T18:00", "2026-10-10", "ready has hour, handover date-only"),
    ("2026-10-10", "2026-10-10T09:00", "ready date-only, handover has hour"),
])
def test_same_day_mixed_precision_is_unproven_and_never_done(staging, event_seq, ready, handover, label):
    """TASK 2 (d,e) — same day but one side lacks an hour: order unprovable."""
    _confirm_sub(event_seq)
    assert _evidence(event_seq, {**_ready_fields(), "entrustment_ready_at": ready},
                     request_id=f"FIX-XP-R-{label}")["ok"]
    before = vm.read_shipment(SHIPMENT)
    outcome = _evidence(event_seq, {**_handover_fields(), "warehouse_handover_at": handover},
                        request_id=f"FIX-XP-H-{label}")
    assert outcome["ok"] is False, label
    assert outcome["gate"] == "ENTRUSTMENT_EVIDENCE_REFUSED"
    assert "chưa chứng minh được" in outcome["error"]
    after = vm.read_shipment(SHIPMENT)
    assert int(after.get("version") or 0) == int(before.get("version") or 0)
    assert stored_entrustment_evidence(after)["handover_at"] == ""


def test_same_day_mixed_precision_already_stored_is_not_done_but_kept(staging, event_seq):
    """Projector side of (d,e): legacy evidence stays, completion fails closed."""
    _confirm_sub(event_seq)
    db = database.get_db()
    document = db["shipments"].find_one({"id": SHIPMENT})
    document["data"]["0.0"]["entrustment_evidence"] = {
        "ready_at": "2026-10-10T18:00", "ready_ref": "HDNT-199/2026",
        "handover_at": "2026-10-10", "handover_from": "FIX-TT",
        "handover_to": "FIX-IMP-A", "handover_doc_no": "BBGN-199-01",
    }
    db["shipments"].replace_one({"id": SHIPMENT}, document)

    row = _shipment_row(vm.build_view_model())
    stages = row["entrustmentStages"]
    assert stages["ready"]["done"] is True
    assert stages["handover"]["done"] is False
    assert any("chưa chứng minh được" in item for item in stages["handover"]["missing"])
    handover_node = _node(row, ENTRUSTMENT_HANDOVER_ID)
    assert handover_node["completed"] is False
    # Evidence preserved verbatim, and repairable by supplying the missing hour.
    assert stages["values"]["warehouse_handover_at"] == "2026-10-10"
    assert stored_entrustment_evidence(vm.read_shipment(SHIPMENT))["handover_doc_no"] == "BBGN-199-01"
    repaired = _evidence(event_seq, {"warehouse_handover_at": "2026-10-10T19:00"},
                         request_id="FIX-XP-REPAIR")
    assert repaired["ok"], repaired.get("error")
    assert _node(_shipment_row(vm.build_view_model()), ENTRUSTMENT_HANDOVER_ID)["completed"] is True


def test_both_date_only_same_day_keeps_the_legacy_contract(staging, event_seq):
    """TASK 2 (f) — date-only/date-only is the legacy contract: equal day is fine."""
    _confirm_sub(event_seq)
    assert _evidence(event_seq, _ready_fields(), request_id="FIX-XP-R6")["ok"]
    outcome = _evidence(event_seq, _handover_fields(), request_id="FIX-XP-H6")
    assert outcome["ok"], outcome.get("error")
    persisted = outcome["persisted"]["entrustmentEvidence"]
    assert persisted["ready_at"] == "2026-10-10"
    assert persisted["handover_at"] == "2026-10-12"
    assert outcome["readback"]["entrustmentStages"]["handover"]["done"] is True


def test_both_datetimes_same_day_use_the_exact_time(staging, event_seq):
    """TASK 2 (g) — both sides carry an hour: compare to the minute."""
    def fresh_case(suffix, handover_time):
        logi_sandbox.reset_backend()
        assert logi_sandbox.ensure_backend() == logi_sandbox.SANDBOX_TRANSPORT
        import streamlit as st
        st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)
        db = database.get_db()
        db["authority_companies"].insert_many([copy.deepcopy(FIXTT), copy.deepcopy(FIX_IMPORTER_A)])
        db["authority_agents"].insert_one(copy.deepcopy(FIX_CONTRACT_B))
        db["contracts"].insert_one(copy.deepcopy(_fixture_contract()))
        _dispatch(event_seq, "shipment_commercial_flow_save",
                  _flow_payload(SHIPMENT, f"FIX-XP-FLOW-{suffix}"))
        assert _evidence(event_seq, {**_ready_fields(), "entrustment_ready_at": "2026-10-10T18:00"},
                         request_id=f"FIX-XP-R7-{suffix}")["ok"]
        return _evidence(event_seq, {**_handover_fields(), "warehouse_handover_at": handover_time},
                         request_id=f"FIX-XP-H7-{suffix}")

    later = fresh_case("LATER", "2026-10-10T19:00")
    assert later["ok"], later.get("error")
    assert later["persisted"]["entrustmentEvidence"]["handover_at"] == "2026-10-10T19:00"
    assert later["readback"]["entrustmentStages"]["handover"]["done"] is True

    earlier = fresh_case("EARLIER", "2026-10-10T17:59")
    assert earlier["ok"] is False
    assert "trước giờ xác nhận" in earlier["error"]
