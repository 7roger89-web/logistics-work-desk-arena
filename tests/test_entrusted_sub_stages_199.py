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
    assert set(ENTRUSTMENT_FIELDS) == {
        "entrustment_ready_at", "entrustment_ready_ref",
        "warehouse_handover_at", "warehouse_handover_from",
        "warehouse_handover_to", "warehouse_handover_doc_no",
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
// exactly what is missing and expose the four bounded fields.
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
    assert out["fieldLabels"] == [
        "Thời điểm bàn giao thực tế", "Bên giao (ghi nhận thực tế)",
        "Bên nhận (ghi nhận thực tế)", "Số biên bản giao nhận",
    ]
    assert "Còn thiếu để xác nhận" in out["missing"]
    assert "bàn giao" in out["missing"].lower()
    assert out["selfReady"] is False and out["selfHandover"] is False
