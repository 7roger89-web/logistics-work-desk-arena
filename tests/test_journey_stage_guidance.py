"""SEA Journey guidance regression: mode/scope/variant and customs truth gates.

Pure tests do not use production DB/network/UI. Writer coercion test imports the
existing viewmodel as in test_logi_gnt_canonical_fields_01.py.
"""
from __future__ import annotations

import pytest

from core.customs_truth import customs_clearance_confirmed
from core.shipment_journey import build_journey
from core.stage_guidance import STAGE_GUIDANCE, guidance_for_node


FIELDS = {"why", "what_to_do", "who", "when", "needs", "done_when", "impact"}
SEA_FCL_IDS = {
    "booking", "pickup", "customs-export", "si-vgm", "gate-in", "etd",
    "on-board", "transit", "arrival", "customs-import", "delivery",
}


def _build(mode: str = "SEA", load: str = "FCL", *, owned: bool = True,
           customs_status=None, delivered: bool = False, sea_facts=None):
    codes = {
        "MAIN_CARRIAGE", "SEA_DOCUMENTS", "AIR_DOCUMENTS", "ORIGIN_HANDOFF",
        "ORIGIN_PICKUP", "EXPORT_HANDLING", "IMPORT_CUSTOMS", "DELIVERY",
    }
    scope = {
        "MAIN_CARRIAGE", "ORIGIN_PICKUP", "EXPORT_HANDLING",
        "ORIGIN_TERMINAL_OR_BORDER", "IMPORT_CUSTOMS", "DESTINATION_TRUCKING",
    } if owned else set()
    profile = {
        "mode": mode, "loadModel": load,
        "serviceScopeConfirmed": owned, "serviceScope": sorted(scope),
        "stages": [{"code": k, "label": k, "reason": "SERVICE_SCOPE"} for k in sorted(codes)],
    }
    shipment = {"id": "STAGE-GUIDANCE-TEST", "data": {
        "1.2": {"sea_export": dict(sea_facts or {}), "air_facts": {}, "road_facts": {}},
        "2.4": {"tk_no": "101", "customs_status": customs_status},
        "2.7": {"is_delivered": delivered},
    }}
    operational = {
        "main_leg": {"booking_no": "BK123", "etd": "2026-10-01",
                     "eta": "2026-10-05", "atd": "", "ata": ""},
        "pickup_leg": {},
    }
    return {n["id"]: n for n in build_journey(
        shipment, profile=profile, operational=operational,
        primary={}, dashboard={}, attachments=[],
    )["nodes"]}


def test_catalog_contains_real_node_ids_and_seven_short_fields():
    # Bước (3B): the catalog now also carries the TWO SUB-only stages, approved
    # for TT_ENTRUSTED_SUB only.  They must obey the same 7-field/120-char
    # contract as every transport node.
    assert set(STAGE_GUIDANCE) == SEA_FCL_IDS | {
        "cfs-receipt", "entrustment-ready", "tt-warehouse-handover",
    }
    for node_id, row in STAGE_GUIDANCE.items():
        assert set(row) == FIELDS, node_id
        assert all(isinstance(v, str) and v.strip() and len(v) <= 120 for v in row.values()), node_id
    lcl = guidance_for_node("si-vgm", load_model="LCL", owned=True)
    assert lcl is not None
    assert set(lcl) == FIELDS
    assert all(len(v) <= 120 for v in lcl.values())


@pytest.mark.parametrize("mode,load,expected,excluded", [
    ("SEA", "FCL", SEA_FCL_IDS, {"cfs-receipt"}),
    ("SEA", "LCL", (SEA_FCL_IDS - {"gate-in"}) | {"cfs-receipt"}, {"gate-in"}),
])
def test_only_real_sea_nodes_get_guidance(mode, load, expected, excluded):
    nodes = _build(mode, load)
    assert expected <= set(nodes)
    assert not (excluded & set(nodes))
    for node_id in expected:
        assert set(nodes[node_id]["guidance"]) == FIELDS
        assert nodes[node_id]["guidance"]["what_to_do"]
        assert nodes[node_id]["guidance"]["done_when"]


@pytest.mark.parametrize("mode", ["AIR", "ROAD", "RAIL"])
def test_non_sea_nodes_never_receive_sea_guidance_even_with_shared_ids(mode):
    nodes = _build(mode)
    for node in nodes.values():
        assert "guidance" not in node, (mode, node["id"])
    assert {"pickup", "customs-export", "customs-import", "delivery"} <= set(nodes)


def test_fcl_lcl_si_text_and_cfs_gate_separated():
    fcl = _build("SEA", "FCL")["si-vgm"]["guidance"]
    lcl = _build("SEA", "LCL")["si-vgm"]["guidance"]
    assert "VGM" in fcl["what_to_do"] and "VGM" in fcl["done_when"]
    assert "SI/VGM" in fcl["who"]
    assert "VGM" not in lcl["what_to_do"]
    assert "VGM" not in lcl["who"] and "bên chịu trách nhiệm SI theo phạm vi" in lcl["who"]
    assert "không yêu cầu VGM" in lcl["done_when"]
    assert "gate_in_at" in _build("SEA", "FCL")["gate-in"]["guidance"]["done_when"]
    assert "consolidated_at" in _build("SEA", "LCL")["cfs-receipt"]["guidance"]["done_when"]


def test_sea_export_facts_editor_title_separates_lcl_si_only_from_fcl_si_vgm():
    from pathlib import Path
    root = Path(__file__).resolve().parent.parent
    journey_tsx = (root / "component/src/components/ShipmentJourney.tsx").read_text(encoding="utf-8")
    dist_js = (root / "component/dist/logi-shell.js").read_text(encoding="utf-8")

    fcl_node = _build("SEA", "FCL")["si-vgm"]
    lcl_node = _build("SEA", "LCL")["si-vgm"]
    assert fcl_node["label"] == "SI / VGM"
    assert any(f["key"].startswith("vgm_") for f in fcl_node["factFields"])
    assert lcl_node["label"] == "SI"
    assert not any(f["key"].startswith("vgm_") for f in lcl_node["factFields"])

    assert "'si-vgm': siOnly ? 'SI — ghi nhận bằng chứng' : 'SI / VGM — ghi nhận bằng chứng'" in journey_tsx
    assert "SI — ghi nhận bằng chứng" in dist_js
    assert "SI / VGM — ghi nhận bằng chứng" in dist_js


def test_sea_export_facts_editor_runtime_dom_separates_lcl_si_only_from_fcl_si_vgm():
    import json
    import os
    import shutil
    import subprocess
    from pathlib import Path
    root = Path(__file__).resolve().parent.parent
    node = shutil.which("node")
    if not node or not (root / "component/node_modules/jsdom").exists():
        pytest.skip("node + component/node_modules/jsdom required for deterministic SeaExportFacts DOM render")

    payload = {
        "fclNodes": list(_build("SEA", "FCL").values()),
        "lclNodes": list(_build("SEA", "LCL").values()),
    }
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
const dom = new JSDOM("<!doctype html><body><div id=\\"host\\"></div>", { url: "http://localhost:9502", pretendToBeVisual: true });
globalThis.window = dom.window; globalThis.document = dom.window.document;
Object.defineProperty(globalThis, "navigator", { value: dom.window.navigator, configurable: true });
for (const k of ["HTMLElement", "HTMLInputElement", "HTMLSelectElement", "HTMLTextAreaElement", "Event", "MouseEvent", "Node", "MutationObserver", "getComputedStyle"]) globalThis[k] = dom.window[k];
dom.window.HTMLElement.prototype.scrollIntoView = function () {};
const mount = (await import(pathToFileURL(path.resolve("component/dist/logi-shell.js")))).default;
const tick = (ms = 120) => new Promise((r) => setTimeout(r, ms));
const waitFor = async (fn, ms = 4000) => {
  const end = Date.now() + ms;
  while (Date.now() < end) { const v = fn(); if (v) return v; await tick(50); }
  return fn();
};
const click = async (el) => { el.dispatchEvent(new MouseEvent("click", { bubbles: true, cancelable: true })); await tick(); };
const text = (el) => el.textContent.replace(/\\s+/g, " ").trim();
const byId = (id) => document.querySelector(`[data-testid="${id}"]`);

const fclVm = structuredClone(base);
fclVm.shipments.find(s => s.id === "SEA-188").journey.nodes = payload.fclNodes;
mount({ name: "logi_shell", data: fclVm, parentElement: document.getElementById("host"), setTriggerValue: () => {} });
await tick(250);
await click([...document.querySelectorAll("a")].find(a => text(a) === "Lô Hàng"));
await click(await waitFor(() => byId("shipment-period-tat-ca")));
await click(await waitFor(() => [...document.querySelectorAll("main a")].find(a => text(a) === "SEA-188")));
await waitFor(() => byId("journey-node-si-vgm"));
await click(byId("journey-node-si-vgm"));
const bubble = await waitFor(() => byId("journey-bubble"));
await click(bubble.querySelector("button[data-testid^=\\"journey-bubble-task-\\"]"));
const fclForm = await waitFor(() => byId("sea-export-facts"));
const fclTitle = text(fclForm.querySelector("h3"));
const fclLabels = [...fclForm.querySelectorAll("select, input")].map(e => e.getAttribute("aria-label")).filter(Boolean);

const lclVm = structuredClone(base);
lclVm.shipments.find(s => s.id === "SEA-188").journey.nodes = payload.lclNodes;
mount({ name: "logi_shell", data: lclVm, parentElement: document.getElementById("host"), setTriggerValue: () => {} });
await tick(250);
const lclForm = await waitFor(() => byId("sea-export-facts"));
const lclTitle = text(lclForm.querySelector("h3"));
const lclLabels = [...lclForm.querySelectorAll("select, input")].map(e => e.getAttribute("aria-label")).filter(Boolean);
console.log(JSON.stringify({ fclTitle, fclLabels, lclTitle, lclLabels }));
"""
    res = subprocess.run(
        [node, "--input-type=module", "-e", script],
        cwd=str(root),
        env=dict(os.environ, NODES_JSON=json.dumps(payload)),
        capture_output=True, text=True, check=True, timeout=60,
    )
    out = json.loads(res.stdout.strip().splitlines()[-1])
    assert out["fclTitle"] == "SI / VGM — ghi nhận bằng chứng"
    assert out["fclLabels"] == ["Trạng thái SI", "Trạng thái VGM", "SI cutoff", "VGM cutoff"]
    assert out["lclTitle"] == "SI — ghi nhận bằng chứng"
    assert out["lclLabels"] == ["Trạng thái SI", "SI cutoff"]


def test_unowned_guidance_is_follow_up_not_fake_assignment():
    nodes = _build("SEA", "FCL", owned=False)
    booking = nodes["booking"]
    assert booking["owned"] is False
    assert "chưa xác nhận" in booking["guidance"]["what_to_do"]
    assert "chưa xác nhận Trường Thành" in booking["guidance"]["who"]
    assert booking["completed"] is False


def test_guidance_is_copy_and_unknown_id_keeps_legacy_payload():
    assert guidance_for_node("air-booking", owned=True) is None
    a = guidance_for_node("booking", owned=True)
    b = guidance_for_node("booking", owned=True)
    assert a is not None and b is not None and a is not b
    a["done_when"] = "tampered"
    assert b["done_when"] == STAGE_GUIDANCE["booking"]["done_when"]


@pytest.mark.parametrize("raw", [None, False, 0, 1, "1", "", "false", "True", "REGISTERED", "SUBMITTED"])
def test_customs_import_not_completed_without_canonical_boolean_true(raw):
    node = _build(customs_status=raw)["customs-import"]
    assert node["completed"] is False, raw
    assert node["state"] != "COMPLETED"


def test_explicit_customs_clearance_true_and_delivery_truth_are_independent():
    nodes = _build(customs_status=True, delivered=True)
    assert nodes["customs-import"]["completed"] is True
    assert nodes["delivery"]["completed"] is True
    assert "POD/trả rỗng" in nodes["delivery"]["guidance"]["what_to_do"]
    assert "POD/trả rỗng" in nodes["delivery"]["guidance"]["done_when"]
    assert nodes["booking"]["completed"] is False


def test_existing_writer_rejects_free_text_customs_status_without_marking_done():
    from views import logi_view_model as vm
    for raw in (False, "false", "0", "", None, 0):
        assert vm._coerce("customs_status", raw) is False
    for raw in (True, "true"):
        assert vm._coerce("customs_status", raw) is True
    for raw in ("1", 1, "True", "REGISTERED", "SUBMITTED", "PENDING", "Đã gửi"):
        with pytest.raises(ValueError):
            vm._coerce("customs_status", raw)


def test_legacy_customs_strings_do_not_turn_other_screens_green():
    # The summary badge, checklist and Journey must agree on clearance truth.
    from views import logi_real_data as rd
    for raw in ("false", "1", "", None, "True", "REGISTERED", "SUBMITTED"):
        shipment = {"id": "LEGACY-CUSTOMS", "data": {
            "1.2": {}, "2.4": {"tk_no": "123456789012", "customs_status": raw},
            "2.6": {}, "2.7": {},
        }}
        assert rd.operational_stage(shipment)[0] == "Chờ thông quan"
        row = next(r for r in rd.document_checklist(shipment)
                   if r["name"] == "Đã thông quan")
        assert row["ok"] is False

    confirmed = {"id": "CONFIRMED-CUSTOMS", "data": {
        "1.2": {}, "2.4": {"tk_no": "123456789012", "customs_status": True},
        "2.6": {}, "2.7": {},
    }}
    assert rd.operational_stage(confirmed)[0] == "Chờ giao"
    row = next(r for r in rd.document_checklist(confirmed)
               if r["name"] == "Đã thông quan")
    assert row["ok"] is True


@pytest.mark.parametrize("raw, expected", [
    (True, True), ("true", True), ("false", False), ("1", False),
    ("", False), (None, False), (False, False), (1, False),
    ("True", False), ("REGISTERED", False),
])
def test_clearance_truth_contract_on_legacy_inputs(raw, expected):
    assert customs_clearance_confirmed(raw) is expected
    assert _build(customs_status=raw)["customs-import"]["completed"] is expected


def test_legacy_customs_string_true_preserves_completed_screens_and_timeline():
    from views import logi_real_data as rd
    for raw in (True, "true"):
        shipment = {"id": "LEGACY-CLEARANCE-TRUE", "data": {
            "1.2": {}, "2.4": {"tk_no": "123456789012", "customs_status": raw},
            "2.6": {}, "2.7": {},
        }}
        assert rd.operational_stage(shipment)[0] == "Chờ giao"
        row = next(r for r in rd.document_checklist(shipment)
                   if r["name"] == "Đã thông quan")
        assert row["ok"] is True
        assert any(m["title"] == "Đã thông quan"
                   for m in rd.tracking_projection(shipment)["milestones"])


def test_false_legacy_values_never_emit_customs_clearance_timeline_milestone():
    from views import logi_real_data as rd
    for raw in ("false", "1", "", None):
        shipment = {"id": "LEGACY-CLEARANCE-FALSE", "data": {
            "1.2": {}, "2.4": {"tk_no": "123456789012", "customs_status": raw},
            "2.6": {}, "2.7": {},
        }}
        assert all(m["title"] != "Đã thông quan"
                   for m in rd.tracking_projection(shipment)["milestones"])
