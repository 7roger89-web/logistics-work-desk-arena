"""LOG-C09 entity-context navigation — current-runtime acceptance.

History: LOG-C09 added Streamlit buttons on the shipment 360 workspace
(``shipment_customer_context_<id>`` …). LOGI-GOOD-V6 removed the Streamlit
workspace entirely: the shipment detail is now a React page and the entity
workspaces are real pages of the SAME shell (``/khach-hang/:id`` and
``/ngu-canh-doi-tac``). The old button keys exist nowhere in ``component/src``
(verified below), so clicking them can no longer mean anything.

What this file still guarantees — the thing LOG-C09 was actually about, i.e.
"from an entity you can reach the real shipment, and vice versa":

* the host mounts with an authenticated session and raises nothing;
* the entity→shipment direction is a bounded READ-ONLY selection
  (``partner_context_select``) whose linked rows carry the EXISTING shipment
  route — proven end-to-end through the real dispatcher + view-model;
* the shipment→entity direction has its DATA delivered on every shipment row
  (customer / legal importer / sub-agent canonical ids), so the shell can link
  it; and the shell declares both entity routes;
* the removed legacy button keys are asserted absent from the component source,
  so a resurrection of the old af­fordance fails here as a contract change.

No production database is touched: the isolated mongomock staging sandbox only.
"""

from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from views import logi_sandbox
from views import logi_view_model as vm

APP_PATH = Path(__file__).resolve().parents[1] / "app.py"
COMPONENT_SRC = Path(__file__).resolve().parents[1] / "component" / "src"

_FIXTURE_USER = {
    "username": "fixture", "display_name": "Fixture", "role": "admin",
    "user_id": "U-FIXTURE", "email": "", "active": True,
}


SHIPMENT = "LO-0308"
AGENT_ID = "AGT-PHUANH"
AMOUNT = 57_000_000.0


class EntityContextMountedTests(unittest.TestCase):
    def setUp(self) -> None:
        import streamlit as st

        logi_sandbox.reset_backend()
        self.assertEqual(logi_sandbox.ensure_backend(), logi_sandbox.SANDBOX_TRANSPORT)
        st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)
        st.session_state.pop(vm.PARTNER_CONTEXT_KEY, None)

    def tearDown(self) -> None:
        import streamlit as st

        st.session_state.pop(vm.PARTNER_CONTEXT_KEY, None)
        logi_sandbox.reset_backend()

    def test_entity_workspace_is_mounted_and_opens_the_linked_shipment(self) -> None:
        # 1. The current host mounts with an authenticated session.
        app = AppTest.from_file(str(APP_PATH), default_timeout=120)
        app.session_state["current_user"] = dict(_FIXTURE_USER)
        with patch("core.database.load_users",
                   return_value={"fixture": dict(_FIXTURE_USER)}):
            app.run()
        self.assertFalse(
            [(e.type, str(e.value)) for e in app.exception],
            msg="mounted host raised",
        )
        self.assertIn(vm.STATE_KEY, app.session_state)
        self.assertTrue(app.session_state[vm.STATE_KEY]["shipments"])

        # 2. Entity → shipment is ONE bounded read-only selection.
        self.assertIn("partner_context_select", vm.ALL_EVENTS)
        self.assertEqual(vm.PARTNER_CONTEXT_EVENTS, {"partner_context_select"})

        slice_ = vm.build_view_model()["partnerContext"]
        self.assertTrue(slice_["readOnly"])
        self.assertTrue(slice_["options"], "the agent master must offer entities")
        self.assertIn(AGENT_ID, {option["key"] for option in slice_["options"]})

        # Give the entity a REAL canonical link to a real shipment (the C2B
        # payable is the canonical partner↔shipment source; nothing invented).
        outcome = vm.consume_phase_b_triggers({"seq": 0}, {"partner_payable_record": {
            "seq": 1, "event": "partner_payable_record",
            "payload": {"shipmentId": SHIPMENT, "partnerId": AGENT_ID,
                        "requestId": "PCX-ENTITY-1", "amount": AMOUNT,
                        "currency": "VND", "note": "Chi phí đối tác"},
        }})[0]
        self.assertTrue(outcome["ok"], outcome["error"])

        selected_event = vm.consume_partner_context_triggers(
            {"seq": 0},
            {"partner_context_select": {
                "seq": 2, "event": "partner_context_select",
                "payload": {"entityKey": f"  {AGENT_ID}  "},
            }},
        )[0]
        self.assertTrue(selected_event["ok"], selected_event)

        selected = vm.build_view_model()["partnerContext"]
        self.assertEqual(selected["selectedKey"], AGENT_ID)  # trimmed, one-shot
        linked = selected.get("shipments") or []
        self.assertTrue(linked, "the selected entity must expose its shipments")
        self.assertEqual([row["shipmentId"] for row in linked], [SHIPMENT])
        # The EXISTING shipment detail route — never a second route.
        self.assertEqual(linked[0]["openHref"], f"/lo-hang/{SHIPMENT}")
        self.assertTrue(linked[0]["canOpen"])
        # A replayed trigger never re-runs the selection.
        self.assertEqual(vm.consume_partner_context_triggers({"seq": 2}, {"partner_context_select": {
            "seq": 2, "event": "partner_context_select",
            "payload": {"entityKey": "AGT-KHAC"},
        }}), [])

    def test_shipment_rows_carry_the_entity_links_the_shell_needs(self) -> None:
        """Shipment → entity: the ids are delivered, the routes are declared."""
        model = vm.build_view_model()
        rows = model["shipments"]
        self.assertTrue(rows)

        flow_keys = set()
        for row in rows:
            self.assertTrue(row.get("customerId") or row.get("customer"), row.get("id"))
            flow = row.get("commercialFlow") or {}
            flow_keys |= set(flow)
        # The three canonical entity dimensions the case cares about (customer,
        # legal importer, sub-agent) are part of the delivered contract.
        for key in ("companyId", "subAgentId", "legalImporterId"):
            self.assertIn(key, flow_keys, f"commercialFlow lost {key}")

        routes = (COMPONENT_SRC / "App.tsx").read_text(encoding="utf-8")
        declared = {chunk.split('"')[0] for chunk in routes.split('<Route path="')[1:]}
        self.assertTrue({"/khach-hang/:id", "/ngu-canh-doi-tac", "/lo-hang/:id"} <= declared)

        # The legacy Streamlit buttons are gone from the component source: if a
        # future change reintroduces an entity affordance it must come with its
        # own current-contract test instead of silently reviving dead keys.
        source = "\n".join(
            p.read_text(encoding="utf-8") for p in COMPONENT_SRC.rglob("*.tsx")
        )
        for legacy_key in (
            "shipment_customer_context_",
            "shipment_factory_context_",
            "shipment_partner_context_",
        ):
            self.assertNotIn(legacy_key, source)


if __name__ == "__main__":
    unittest.main()
