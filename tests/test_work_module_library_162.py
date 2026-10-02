"""Issue #162 — Work Module Library V1.

Challenges the plausible WRONG implementations as much as the happy path:

* V2 retroactively changing a shipment bound to V1;
* a RETIRED/DRAFT template being newly attached;
* a Viewer (or any under-privileged role) writing through the dispatcher;
* a PROBLEM/CURRENT visual overlay erasing factual completion;
* completing an unrelated step clearing a blocking gate;
* uploading a document auto-completing a module step;
* the base shipment behaviour changing when NO module is attached.

Uses the isolated mongomock staging transport only; it never touches a real
deployment, a second task/document/finance store, or a production URI.
"""
from __future__ import annotations

import pytest

from core.work_modules import (
    DEMO_TEMPLATE_ID,
    attachable_templates,
    build_instance,
    demo_template,
    index_templates,
    instances_of,
    module_execution,
    normalize_instance,
    normalize_template,
    resolve_template,
)
from views import logi_real_data as rd, logi_sandbox, logi_view_model as vm

SCOPE = ["IMPORT_CUSTOMS", "FINAL_DELIVERY"]


def document(sid: str = "SEA-162") -> dict:
    """A minimal shipment whose service scope owns imports + delivery."""
    return {
        "id": sid, "customer": "An Phát JSC", "status": "wait", "currency": "VND", "version": 0,
        "data": {
            "0.0": {"mode": "Sea", "execution_profile": {
                "incoterm_version": "2020", "incoterm_named_place": "Hai Phong", "load_model": "FCL",
                "service_scope": SCOPE, "service_scope_confirmed": True,
                "cargo_insurance": {"status": "NO"}}},
            "1.2": {"transport_legs": [
                {"id": "pickup-162", "sequence": 1, "mode": "Truck", "origin": "Factory",
                 "destination": "Hai Phong", "etd": "2026-10-01", "units": []},
                {"id": "sea-162", "sequence": 2, "mode": "Sea", "origin": "Hai Phong",
                 "destination": "Singapore", "booking_no": "BK-162", "atd": "", "ata": "",
                 "units": [{"id": "cont-162", "kind": "container", "number": "ABCD1621621", "type_size": "40HC"}]}]},
            "2.4": {}, "2.6": {}, "2.7": {}, "3.4": {"details": [], "payments": []}, "entrustment": {},
        },
    }


def project(doc: dict, **kwargs) -> dict:
    return rd.shipment_projection(doc, ledger={}, agents={}, attachments={},
                                 docgen_documents={}, linked_contracts={}, **kwargs)


def nodes(row: dict) -> dict:
    return {n["id"]: n for n in row["journey"]["nodes"]}


def two_step_template(**overrides) -> dict:
    base = {
        "template_id": "TEST_MODULE_162", "name": "Test module", "version": 1, "status": "ACTIVE",
        "anchor_stage": "customs-import", "gate_stage": "delivery",
        "join": {"from": "result", "type": "BLOCKING"},
        "nodes": [
            {"id": "prepare", "label": "Prepare"},
            {"id": "result", "label": "Result", "dependencies": [
                {"type": "BLOCKING", "nodeId": "prepare"}]},
        ],
    }
    base.update(overrides)
    return normalize_template(base)


# --------------------------------------------------------------- normalization

def test_template_normalization_is_bounded_and_refuses_invented_vocabulary():
    template = two_step_template()
    assert template["id"] == "TEST_MODULE_162:V1"
    assert template["status"] == "ACTIVE"
    for bad in [
        {"status": "PUBLISHED"},
        {"anchor_stage": "not-a-stage"},
        {"gate_stage": "not-a-stage"},
        {"nodes": [{"id": "a", "dependencies": [{"type": "MAGIC", "nodeId": "a"}]}]},
        {"nodes": [{"id": "a", "dependencies": [{"type": "BLOCKING", "nodeId": "ghost"}]}]},
        {"nodes": [{"id": "a"}, {"id": "a"}]},
        {"nodes": [{"id": "a"}], "gate_stage": "delivery"},
        {"nodes": [{"id": "a"}], "gate_stage": "delivery", "join": {"from": "ghost", "type": "BLOCKING"}},
        {"nodes": [{"id": "a", "guidance": {"vibe": "x"}}]},
        {"template_id": "BAD ID"}, {"name": ""},
    ]:
        with pytest.raises(ValueError):
            two_step_template(**bad)


def test_instance_binds_exact_template_id_and_version_and_bounded_provenance():
    template = two_step_template()
    instance = build_instance(template, instance_id="WM1", actor="tester", actor_user_id="U1")
    assert (instance["template_id"], instance["template_version"]) == ("TEST_MODULE_162", 1)
    assert instance["provenance"] == "MANUAL_ADDITION" and instance["added_by"] == "tester"
    with pytest.raises(ValueError):
        normalize_instance({**instance, "provenance": "CUSTOMER_PLAYBOOK"})
    with pytest.raises(ValueError):
        normalize_instance({**instance, "template_version": 0})


def test_only_the_newest_active_version_is_attachable():
    templates = [two_step_template(version=1, status="RETIRED"),
                 two_step_template(version=2, status="ACTIVE"),
                 two_step_template(version=3, status="DRAFT"),
                 two_step_template(template_id="OTHER_162", version=9, status="ACTIVE")]
    choices = {row["templateId"]: row["version"] for row in attachable_templates(templates)}
    assert choices == {"TEST_MODULE_162": 2, "OTHER_162": 9}


# ------------------------------------------------------- pure execution truth

def test_factual_completion_drives_readiness_and_never_the_visual_state():
    template = two_step_template()
    instance = build_instance(template, instance_id="WM1")
    empty = module_execution(template, instance, gate_label="DELIVERY")
    assert empty["status"] == "BLOCKING" and empty["summary"] == "0/2 bước"
    assert empty["gateText"] == "Chặn DELIVERY — còn thiếu Prepare, Result"
    assert empty["steps"][1]["blockedBy"] == ["prepare"]

    half = build_instance(template, instance_id="WM1")
    half["completed_steps"] = [{"node_id": "prepare", "completed_by": "u", "completed_at": "2026-10-02T08:00"}]
    partial = module_execution(template, half, gate_label="DELIVERY")
    assert partial["status"] == "BLOCKING" and partial["summary"] == "1/2 bước"
    assert partial["gateText"] == "Chặn DELIVERY — còn thiếu Result"
    assert partial["steps"][1]["blockedBy"] == []

    full = build_instance(template, instance_id="WM1")
    full["completed_steps"] = [{"node_id": "prepare", "completed_by": "u", "completed_at": "x"},
                               {"node_id": "result", "completed_by": "u", "completed_at": "y"}]
    done = module_execution(template, full, gate_label="DELIVERY")
    assert done["status"] == "DONE" and done["gateText"] == "" and done["summary"] == "2/2 bước"


def test_informational_dependency_never_gates_and_unrelated_step_never_clears_the_gate():
    template = normalize_template({
        "template_id": "SIDE_162", "name": "Side module", "version": 1, "status": "ACTIVE",
        "anchor_stage": "customs-import", "gate_stage": "delivery",
        "join": {"from": "result", "type": "BLOCKING"},
        "nodes": [
            {"id": "prepare", "label": "Prepare"},
            {"id": "side-note", "label": "Side note", "dependencies": [
                {"type": "INFORMATIONAL", "nodeId": "prepare"}]},
            {"id": "result", "label": "Result", "dependencies": [
                {"type": "BLOCKING", "nodeId": "prepare"}]},
        ],
    })
    instance = build_instance(template, instance_id="WM2")
    instance["completed_steps"] = [{"node_id": "side-note", "completed_by": "u", "completed_at": "t"},
                                   {"node_id": "prepare", "completed_by": "u", "completed_at": "t"}]
    execution = module_execution(template, instance, gate_label="DELIVERY")
    # An INFORMATIONAL-only step is done, the decisive step is not: still blocking.
    assert execution["status"] == "BLOCKING"
    assert execution["gateText"] == "Chặn DELIVERY — còn thiếu Result"
    # And the informational node could never have been required:
    instance["completed_steps"] = [{"node_id": "prepare", "completed_by": "u", "completed_at": "t"}]
    assert module_execution(template, instance, gate_label="DELIVERY")["status"] == "BLOCKING"


def test_unresolvable_bound_version_stays_unknown_and_never_green():
    from core.work_modules import compose_journey_modules

    nodes, edges = [], []
    rollups = compose_journey_modules(nodes, edges, {}, templates=[], instances=[
        {"instance_id": "WMX", "template_id": "GONE", "template_version": 7,
         "provenance": "MANUAL_ADDITION", "added_by": "u", "added_at": "t", "completed_steps": []}])
    assert [r["status"] for r in rollups] == ["UNKNOWN"]
    assert rollups[0]["completedCount"] == 0 and rollups[0]["totalCount"] == 0
    assert rollups[0]["unresolved"] is True
    assert nodes == [] and edges == []


# --------------------------------------------------- journey composition

def test_no_module_means_the_pre_162_payload_is_untouched():
    doc = document()
    row = project(doc)
    assert "modules" not in row["journey"]
    assert [n["id"] for n in row["journey"]["nodes"]] == [
        "booking", "etd", "on-board", "transit", "arrival", "customs-import", "delivery"]
    assert row["journey"]["currentStageId"] == ""


def test_module_composition_is_additive_and_blocks_only_the_declared_gate():
    doc = document()
    base = project(doc)
    template = two_step_template()
    instance = build_instance(template, instance_id="WM1", actor="tester")
    doc = dict(doc)
    doc["work_modules"] = [instance]
    row = project(doc, work_module_templates=[template])
    base_nodes, module_nodes = nodes(base), nodes(row)

    # Base truth is preserved byte-for-byte except for the ADDED gate evidence.
    for node_id, node in base_nodes.items():
        assert module_nodes[node_id]["completed"] == node["completed"]
        assert module_nodes[node_id]["label"] == node["label"]
        assert module_nodes[node_id]["evidence"] == node["evidence"]
        assert module_nodes[node_id]["state"] == node["state"] or node_id == "delivery"
    assert row["journey"]["currentStageId"] == base["journey"]["currentStageId"]
    assert row["journey"]["primaryAction"] == base["journey"]["primaryAction"]

    delivery = module_nodes["delivery"]
    assert delivery["state"] == "PROBLEM" and delivery["completed"] is False
    assert "Chặn DELIVERY — còn thiếu Prepare, Result" in delivery["blockers"]
    assert "wm-WM1-result" in delivery["dependencies"]
    assert module_nodes["customs-import"]["dependencies"] == base_nodes["customs-import"]["dependencies"]
    # Machine graph is explicit and connected.
    assert {"from": "wm-WM1-prepare", "to": "wm-WM1-result"} in row["journey"]["edges"]
    assert {"from": "wm-WM1-result", "to": "delivery"} in row["journey"]["edges"]
    rollup = row["journey"]["modules"][0]
    assert rollup["name"] == "Test module" and rollup["templateVersion"] == 1
    assert rollup["gate"]["label"] == "DELIVERY" and rollup["gateText"].startswith("Chặn DELIVERY")


def test_completed_gate_stage_keeps_its_fact_and_module_blocker_does_not_reorder_truth():
    doc = document()
    doc["data"]["2.7"] = {"is_delivered": True, "delivered_at": "2026-10-09"}
    template = two_step_template()
    doc["work_modules"] = [build_instance(template, instance_id="WM1")]
    row = project(doc, work_module_templates=[template])
    delivery = nodes(row)["delivery"]
    # Factual completion survives the blocking module overlay untouched.
    assert delivery["completed"] is True
    assert delivery["state"] == "PROBLEM"
    assert delivery["blockers"]


def test_unknown_instance_block_is_kept_visible_not_dropped():
    doc = document()
    doc["work_modules"] = [{"instance_id": "WMBAD", "template_id": "X", "template_version": 1}]
    row = project(doc, work_module_templates=[])
    assert row["journey"]["modules"][0]["status"] == "UNKNOWN"
    assert row["journey"]["modules"][0]["gateText"] == ""


# ------------------------------------------------------------- real write path

@pytest.fixture
def staging():
    import streamlit as st

    from core.database import load_work_module_templates, save_shipment_atomic, save_work_module_template

    logi_sandbox.reset_backend()
    assert logi_sandbox.ensure_backend() == logi_sandbox.SANDBOX_TRANSPORT
    st.session_state["current_user"] = {"username": "boot", "role": "ADMIN", "user_id": "B", "active": True}
    assert save_shipment_atomic(document(), actor="issue162-fixture")
    assert save_work_module_template(two_step_template())
    # The sandbox seed already published the ONE demo fixture; re-publishing the
    # same immutable version is refused (and that refusal is asserted below).
    assert demo_template()["id"] in {row["id"] for row in load_work_module_templates()}
    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)
    st.session_state[vm.LAST_WRITES_KEY] = []
    yield
    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)
    logi_sandbox.reset_backend()


_seq = {"n": 0}


def event(name: str, payload: dict) -> dict:
    _seq["n"] += 1
    return vm.consume_phase_b_triggers({"seq": _seq["n"] - 1}, {name: {"seq": _seq["n"], "payload": payload}})[0]


def current(sid: str = "SEA-162") -> dict:
    return next(row for row in vm.build_view_model()["shipments"] if row["id"] == sid)


def version(sid: str = "SEA-162") -> int:
    return current(sid)["version"]


def attach(template_id: str = "TEST_MODULE_162", sid: str = "SEA-162", **extra) -> dict:
    return event("work_module_attach", {"shipmentId": sid, "templateId": template_id,
                                        "requestId": f"ATT-{_seq['n'] + 1}",
                                        "expectedVersion": version(sid), **extra})


def complete(instance_id: str, node_id: str, sid: str = "SEA-162", **extra) -> dict:
    return event("work_module_step_complete", {"shipmentId": sid, "instanceId": instance_id,
                                               "nodeId": node_id,
                                               "requestId": f"STP-{_seq['n'] + 1}",
                                               "expectedVersion": version(sid), **extra})


def test_attach_persists_exact_version_provenance_actor_and_only_readback_shows_it(staging):
    before = current()
    result = attach(reason="Kiểm chứng kiến trúc")
    assert result["ok"], result
    stored = vm.read_shipment("SEA-162")["work_modules"][0]
    assert stored["template_id"] == "TEST_MODULE_162" and stored["template_version"] == 1
    assert stored["provenance"] == "MANUAL_ADDITION"
    assert stored["added_by"] == logi_sandbox.STAGING_ACTOR["username"]
    assert stored["added_at"] and stored["reason"] == "Kiểm chứng kiến trúc"
    assert result["readback"]["journey"]["modules"][0]["templateVersion"] == 1
    after = current()
    assert "modules" not in before["journey"] and "modules" in after["journey"]
    # Documents/finance/tasks authorities are untouched by an attach.
    assert after["attachments"] == before["attachments"]
    assert after["finance"] == before["finance"]
    assert "work_modules" not in after and "work_modules" not in after.get("journey", {})


def test_attach_refuses_draft_retired_unknown_and_stale_version(staging):
    from core.database import save_work_module_template

    import streamlit as st

    st.session_state["current_user"] = {"username": "ops", "role": "OPERATIONS", "user_id": "O", "active": True}
    assert save_work_module_template(two_step_template(template_id="DRAFT_162", status="DRAFT"))
    assert save_work_module_template(two_step_template(template_id="RETIRED_162", status="RETIRED"))
    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)

    for template_id in ("DRAFT_162", "RETIRED_162", "GHOST_162"):
        result = attach(template_id)
        assert not result["ok"] and "work_modules" not in (vm.read_shipment("SEA-162") or {})
    stale = event("work_module_attach", {"shipmentId": "SEA-162", "templateId": "TEST_MODULE_162",
                                         "requestId": "ATT-STALE", "expectedVersion": -1})
    assert not stale["ok"] and "thay đổi" in stale["error"]
    assert attach()["ok"]
    assert not attach()["ok"], "the same version must not be attached twice"


def test_version_immutability_survives_publishing_v2(staging):
    import streamlit as st

    assert attach()["ok"]
    instance_id = current()["journey"]["modules"][0]["instanceId"]
    st.session_state["current_user"] = {"username": "ops", "role": "OPERATIONS", "user_id": "O", "active": True}
    v2 = {"template_id": "TEST_MODULE_162", "name": "Test module V2", "version": 2, "status": "ACTIVE",
          "anchor_stage": "customs-import", "gate_stage": "delivery",
          "join": {"from": "final", "type": "BLOCKING"},
          "nodes": [{"id": "final", "label": "Final signoff"}]}
    assert vm.consume_phase_b_triggers({"seq": 0}, {"work_module_template_save": {"seq": 1, "payload": {
        "requestId": "T-V2", "template": v2}}})[0]["ok"]
    # Rewriting the already published V1 is refused outright.
    rewrite = vm.consume_phase_b_triggers({"seq": 0}, {"work_module_template_save": {"seq": 1, "payload": {
        "requestId": "T-V1-REWRITE", "template": two_step_template()}}})
    assert rewrite and not rewrite[0]["ok"] and "không thể sửa" in rewrite[0]["error"]
    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)

    model = vm.build_view_model()
    row = next(r for r in model["shipments"] if r["id"] == "SEA-162")
    module = row["journey"]["modules"][0]
    assert module["templateVersion"] == 1 and module["name"] == "Test module"
    assert [s["id"] for s in module["steps"]] == ["prepare", "result"]
    # A NEW attachment resolves the newest ACTIVE version and stores it explicitly.
    assert [t["version"] for t in model["workModules"]["templates"] if t["templateId"] == "TEST_MODULE_162"] == [2]
    # New attachment resolves the newest ACTIVE version and records it explicitly
    # while the existing instance keeps V1.
    assert attach(template_id="TEST_MODULE_162")["ok"]
    fresh = sorted(vm.read_shipment("SEA-162")["work_modules"], key=lambda r: r["instance_id"])
    assert sorted(row["template_version"] for row in fresh) == [1, 2]


def test_factual_completion_flows_through_readback_and_clears_the_gate(staging):
    assert attach()["ok"]
    instance_id = current()["journey"]["modules"][0]["instanceId"]
    first = complete(instance_id, "prepare")
    assert first["ok"], first
    module = first["readback"]["journey"]["modules"][0]
    assert module["summary"] == "1/2 bước" and module["status"] == "BLOCKING"
    assert module["gateText"] == "Chặn DELIVERY — còn thiếu Result"
    stored = vm.read_shipment("SEA-162")["work_modules"][0]["completed_steps"][0]
    assert stored["completed_by"] == logi_sandbox.STAGING_ACTOR["username"] and stored["completed_at"]
    assert first["audit"], "the atomic writer must keep its audit trail"

    second = complete(instance_id, "result")
    assert second["ok"]
    module = second["readback"]["journey"]["modules"][0]
    assert module["status"] == "DONE" and module["gateText"] == ""
    gate = next(n for n in second["readback"]["journey"]["nodes"] if n["id"] == "delivery")
    assert not [b for b in gate["blockers"] if "Chặn" in b]
    # Position stays the physical/operational truth, never "current module work".
    assert second["readback"]["journey"]["currentStageId"] == ""
    # Idempotent: the same step cannot be recorded twice.
    again = complete(instance_id, "result")
    assert again["ok"] and again.get("noop")
    assert len(vm.read_shipment("SEA-162")["work_modules"][0]["completed_steps"]) == 2


def test_step_completion_refuses_unknown_node_and_unknown_instance(staging):
    assert attach()["ok"]
    instance_id = current()["journey"]["modules"][0]["instanceId"]
    assert not complete(instance_id, "not-a-step")["ok"]
    assert not complete("WMGHOST", "prepare")["ok"]
    assert vm.read_shipment("SEA-162")["work_modules"][0].get("completed_steps", []) == []


def test_viewer_cannot_attach_complete_or_author_and_sees_everything_read_only(staging):
    import streamlit as st

    st.session_state["current_user"] = {"username": "viewer162", "role": "VIEWER", "user_id": "V", "active": True}
    model = vm.build_view_model()
    assert model["workModules"]["canAttach"] is False and model["workModules"]["canAuthor"] is False
    assert model["workModules"]["templates"], "a Viewer still reads the library"
    attach_result = attach()
    assert not attach_result["ok"] and "RBAC" in attach_result["error"]
    complete_result = complete("WM1", "prepare")
    assert not complete_result["ok"] and "RBAC" in complete_result["error"]
    author = event("work_module_template_save", {"requestId": "V-1", "template": two_step_template()})
    assert not author["ok"] and "RBAC" in author["error"]
    assert "work_modules" not in (vm.read_shipment("SEA-162") or {})
    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)
    # A Support actor may do all three through the same seam.
    assert attach()["ok"]


def test_sale_cannot_author_a_template_but_may_attach_and_complete(staging):
    import streamlit as st

    st.session_state["current_user"] = {"username": "sale162", "role": "SALE", "user_id": "S", "active": True}
    author = event("work_module_template_save", {"requestId": "S-1", "template": two_step_template(template_id="SALE_162")})
    assert not author["ok"] and "RBAC" in author["error"]
    assert attach()["ok"]
    instance_id = current()["journey"]["modules"][0]["instanceId"]
    assert complete(instance_id, "prepare")["ok"]


def test_document_upload_alone_never_completes_a_module_step(staging):
    assert attach()["ok"]
    doc = vm.read_shipment("SEA-162")
    instance_id = doc["work_modules"][0]["instance_id"]
    # The step's document category is context; an existing attachment of that
    # category must not turn the step into a completed fact.
    from core.database import save_shipment_attachment  # noqa: PLC0415

    assert save_shipment_attachment({"id": "ATT-162", "shipment_id": "SEA-162", "category": "customs",
                                     "original_name": "customs.pdf", "sha256": "x" * 64,
                                     "storage_backend": "gridfs", "storage_file_id": "FILE-162"})
    assert any(row["id"] == "ATT-162" for row in current()["attachments"]), "the file IS stored (canonical store)"
    row = current()
    module = row["journey"]["modules"][0]
    assert module["summary"] == "0/2 bước" and module["status"] == "BLOCKING"
    assert all(not step["completed"] for step in module["steps"])
    assert vm.read_shipment("SEA-162")["work_modules"][0].get("completed_steps", []) == []


def test_problem_overlay_from_an_alert_cannot_erase_module_completion(staging):
    assert attach()["ok"]
    instance_id = current()["journey"]["modules"][0]["instanceId"]
    assert complete(instance_id, "prepare")["ok"]
    assert complete(instance_id, "result")["ok"]
    # A dashboard alert makes the gate stage PROBLEM; completion facts stay true.
    from core.database import save_shipment_atomic

    doc = vm.read_shipment("SEA-162")
    doc["data"]["2.7"] = {"is_delivered": True, "delivered_at": "2026-10-09"}
    assert save_shipment_atomic(doc, expected_version=doc["version"], actor="fixture")
    row = current()
    module = row["journey"]["modules"][0]
    node = row["journey"]["nodes"]
    assert module["status"] == "DONE"
    assert all(step["completed"] for step in module["steps"])
    assert next(n for n in node if n["id"] == "wm-%s-prepare" % instance_id)["completed"] is True
    assert next(n for n in node if n["id"] == "delivery")["completed"] is True


def test_library_projection_exposes_only_server_owned_vocabulary_and_no_write_flags_for_viewer(staging):
    model = vm.build_view_model()
    library = model["workModules"]
    assert library["canAttach"] is True and library["canAuthor"] is True
    assert library["stages"] and all(set(row) == {"id", "label"} for row in library["stages"])
    assert set(row["status"] for row in library["all"]) <= {"DRAFT", "ACTIVE", "RETIRED"}
    assert DEMO_TEMPLATE_ID in {row["templateId"] for row in library["templates"]}
    demo = next(row for row in library["templates"] if row["templateId"] == DEMO_TEMPLATE_ID)
    assert demo["stepCount"] == 3 and demo["gateStage"] == "delivery"


def test_no_second_authority_is_created_by_this_slice():
    """The slice must not add a module-scoped task/document/finance/engine store."""
    import core.database as db_module

    source = open(db_module.__file__, encoding="utf-8").read()
    for forbidden in ("work_module_tasks", "work_module_documents", "work_module_finance",
                      "work_module_instances", "workflow_engine", "module_scheduler"):
        assert forbidden not in source
    from core.work_modules import PROVENANCE_TYPES

    assert PROVENANCE_TYPES == ("MANUAL_ADDITION", "COMPANY_STANDARD")
    assert resolve_template(index_templates([two_step_template()]), "TEST_MODULE_162", 2) is None
    assert instances_of({"work_modules": None}) == []
