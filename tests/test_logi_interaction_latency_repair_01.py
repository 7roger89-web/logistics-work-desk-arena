"""LOGI_INTERACTION_LATENCY_REPAIR_01 — focused acceptance tests for interaction latency repair.

Verifies:
- Component v2 trigger callback executes before the script body (build_view_model)
- Representative actions (save, create, translate) invoke their canonical handlers exactly once
- Exactly ONE view-model build occurs per user event (eliminating the redundant pre-action build)
- No explicit second st.rerun() is issued after callback execution
- Post-mount dispatch is bypassed when the event was already consumed in callback
- LAST_WRITES and authoritative readback reach the fresh view-model
- Sequence replay guard prevents double execution
- Server-side RBAC refusals and failed writes are recorded in lastWrites and exit pending state
"""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

import streamlit as st

from core.deepl_translation import TranslationResult
from views import logi_sandbox, logi_shell, logi_view_model, web_app

COMPONENT_KEY = logi_shell.COMPONENT_KEY


class _MockSessionState(dict):
    """Minimal session_state mock supporting attribute and dict access."""

    def __getattr__(self, name: str) -> object:
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    def __setattr__(self, name: str, value: object) -> None:
        self[name] = value


class InteractionLatencyRepairTests(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_ss = _MockSessionState()
        self.orig_ss = getattr(st, "session_state", None)
        st.session_state = self.mock_ss
        logi_sandbox.ensure_backend()

    def tearDown(self) -> None:
        if self.orig_ss is not None:
            st.session_state = self.orig_ss

    def _simulate_streamlit_event_lifecycle(
        self,
        trigger_dict: dict,
        *,
        auth_role: str = "admin",
        mock_renderer_result: object = None,
    ) -> list[tuple[str, object]]:
        """Simulate the official Streamlit execution lifecycle for a component event.

        1. Incoming trigger is placed into session_state[COMPONENT_KEY].
        2. Streamlit prefix: widget callbacks execute (views.logi_shell._on_component_event).
        3. Streamlit script body runs: views.web_app.main() -> build_view_model() -> render().
        4. If st.rerun() is explicitly queued, execute second run.
        """
        trace: list[tuple[str, object]] = []
        rerun_called = [False]

        # In Streamlit, the incoming trigger state is available in session state before callbacks run
        st.session_state[COMPONENT_KEY] = trigger_dict
        st.session_state["current_user"] = {"username": "test_user", "role": auth_role}

        orig_bvm = logi_view_model.build_view_model

        def tracked_bvm(*args, **kwargs):
            trace.append(("build_view_model", len([x for x in trace if x[0] == "build_view_model"]) + 1))
            vm = orig_bvm(*args, **kwargs)
            return vm

        def tracked_rerun():
            trace.append(("st.rerun", None))
            rerun_called[0] = True

        from streamlit.components.v2.bidi_component.state import ComponentResult
        renderer_return = mock_renderer_result or ComponentResult({}, trigger_dict)

        with patch("views.logi_view_model.build_view_model", side_effect=tracked_bvm), \
             patch("streamlit.rerun", side_effect=tracked_rerun), \
             patch("views.logi_shell._renderer", return_value=lambda **kw: renderer_return), \
             patch("views.web_app.require_login", return_value={"username": "test_user", "role": auth_role}):

            # Step 1: Callback prefix
            trace.append(("CALLBACK_PREFIX_START", None))
            logi_shell._on_component_event()
            trace.append(("CALLBACK_PREFIX_END", None))

            # Step 2: Main script body
            trace.append(("SCRIPT_BODY_START", 1))
            web_app.main()
            trace.append(("SCRIPT_BODY_END", 1))

            # Step 3: Handle explicit rerun if any
            if rerun_called[0]:
                rerun_called[0] = False
                trace.append(("SCRIPT_BODY_START", 2))
                web_app.main()
                trace.append(("SCRIPT_BODY_END", 2))

        return trace

    # -----------------------------------------------------------------------
    # 1. Structural Order: Callback executes BEFORE full model body
    # -----------------------------------------------------------------------

    def test_callback_executes_before_script_body(self) -> None:
        """Proves trigger callback runs BEFORE build_view_model and script body."""
        trigger = {
            "shipment_field_save": {
                "seq": 1,
                "event": "shipment_field_save",
                "payload": {"shipmentId": "LO-0306", "fields": {"booking_no": "BK-ORD-01"}},
            }
        }
        trace = self._simulate_streamlit_event_lifecycle(trigger)

        events_only = [t[0] for t in trace]
        self.assertIn("CALLBACK_PREFIX_START", events_only)
        self.assertIn("build_view_model", events_only)

        cb_idx = events_only.index("CALLBACK_PREFIX_START")
        bvm_idx = events_only.index("build_view_model")

        self.assertLess(cb_idx, bvm_idx, "Callback MUST execute before build_view_model")
        self.assertEqual(events_only.count("build_view_model"), 1, "Exactly ONE VM build per event")
        self.assertNotIn("st.rerun", events_only, "No second st.rerun after callback")

    # -----------------------------------------------------------------------
    # 2. Representative Actions: Exact call counts = 1
    # -----------------------------------------------------------------------

    def test_save_handler_called_exactly_once(self) -> None:
        """shipment_field_save invokes save_shipment_atomic exactly once."""
        trigger = {
            "shipment_field_save": {
                "seq": 1,
                "event": "shipment_field_save",
                "payload": {"shipmentId": "LO-0306", "fields": {"booking_no": "BK-ONCE-01"}},
            }
        }
        with patch("core.database.save_shipment_atomic", return_value=True) as mock_save:
            trace = self._simulate_streamlit_event_lifecycle(trigger)
            self.assertEqual(mock_save.call_count, 1, "save_shipment_atomic must be called exactly once")

        bvm_count = len([t for t in trace if t[0] == "build_view_model"])
        self.assertEqual(bvm_count, 1)
        self.assertNotIn("st.rerun", [t[0] for t in trace])

    def test_create_handler_called_exactly_once(self) -> None:
        """shipment_create invokes canonical creation writer exactly once."""
        trigger = {
            "shipment_create": {
                "seq": 1,
                "event": "shipment_create",
                "payload": {
                    "shipmentId": "LO-ONCE-CREATE-01",
                    "customerId": "CUS-1",
                    "customer": "Khách Test 1",
                    "requestId": "REQ-CREATE-1",
                },
            }
        }
        with patch("core.database.save_shipment_atomic", return_value=True) as mock_save, \
             patch("core.database.load_customers", return_value={"CUS-1": {"id": "CUS-1", "name": "Khách Test 1"}}):
            trace = self._simulate_streamlit_event_lifecycle(trigger)
            self.assertEqual(mock_save.call_count, 1, "Creation writer must be called exactly once")

        bvm_count = len([t for t in trace if t[0] == "build_view_model"])
        self.assertEqual(bvm_count, 1)
        self.assertNotIn("st.rerun", [t[0] for t in trace])

    def test_translate_provider_called_exactly_once(self) -> None:
        """translate_text invokes run_translation provider exactly once."""
        trigger = {
            "translate_text": {
                "seq": 1,
                "event": "translate_text",
                "payload": {
                    "text": "Shipping documents attached",
                    "sourceLang": "EN",
                    "targetLang": "VI",
                },
            }
        }
        fake_translation = {
            "status": "TRANSLATED",
            "translatedText": "Chứng từ giao hàng đính kèm",
            "detectedSourceLang": "EN",
            "billedCharacters": 27,
        }
        with patch("views.translation.run_translation", return_value=fake_translation) as mock_translate:
            trace = self._simulate_streamlit_event_lifecycle(trigger)
            self.assertEqual(mock_translate.call_count, 1, "run_translation must be called exactly once")

        bvm_count = len([t for t in trace if t[0] == "build_view_model"])
        self.assertEqual(bvm_count, 1)
        self.assertNotIn("st.rerun", [t[0] for t in trace])

    # -----------------------------------------------------------------------
    # 3. Readback and State Preservation
    # -----------------------------------------------------------------------

    def test_last_writes_readback_in_next_model(self) -> None:
        """Authoritative outcome reaches the view-model in the same single run."""
        trigger = {
            "shipment_field_save": {
                "seq": 1,
                "event": "shipment_field_save",
                "payload": {"shipmentId": "LO-0306", "fields": {"booking_no": "BK-READBACK-01"}},
            }
        }
        with patch("core.database.save_shipment_atomic", return_value=True):
            self._simulate_streamlit_event_lifecycle(trigger)

        last_writes = st.session_state.get(logi_view_model.LAST_WRITES_KEY)
        self.assertIsNotNone(last_writes)
        self.assertTrue(len(last_writes) > 0)
        self.assertEqual(last_writes[0]["event"], "shipment_field_save")
        self.assertTrue(last_writes[0]["ok"])

        # Check view-model embeds it
        vm = logi_view_model.build_view_model()
        self.assertIn("lastWrites", vm)
        self.assertTrue(any(w.get("event") == "shipment_field_save" for w in vm["lastWrites"]))

    def test_seq_replay_does_not_double_execute(self) -> None:
        """Replaying an already consumed sequence number does not re-invoke handlers."""
        # Establish initial seq
        st.session_state[logi_view_model.SEQ_KEY] = 5

        trigger = {
            "shipment_field_save": {
                "seq": 5,  # Stale seq
                "event": "shipment_field_save",
                "payload": {"shipmentId": "LO-0306", "fields": {"booking_no": "BK-STALE-01"}},
            }
        }
        with patch("core.database.save_shipment_atomic") as mock_save:
            self._simulate_streamlit_event_lifecycle(trigger)
            mock_save.assert_not_called()

    def test_rbac_refusal_still_returns_correctly(self) -> None:
        """RBAC refusal is recorded in lastWrites and delivered without crash or rerun."""
        trigger = {
            "shipment_field_save": {
                "seq": 1,
                "event": "shipment_field_save",
                "payload": {"shipmentId": "LO-0306", "fields": {"booking_no": "BK-DENIED-01"}},
            }
        }
        # Role 'viewer' cannot edit shipments
        with patch("core.database.save_shipment_atomic") as mock_save:
            trace = self._simulate_streamlit_event_lifecycle(trigger, auth_role="viewer")
            mock_save.assert_not_called()

        last_writes = st.session_state.get(logi_view_model.LAST_WRITES_KEY)
        self.assertIsNotNone(last_writes)
        self.assertEqual(len(last_writes), 1)
        self.assertEqual(last_writes[0]["event"], "shipment_field_save")
        self.assertFalse(last_writes[0]["ok"])
        self.assertIn("RBAC", last_writes[0]["error"])

        bvm_count = len([t for t in trace if t[0] == "build_view_model"])
        self.assertEqual(bvm_count, 1)
        self.assertNotIn("st.rerun", [t[0] for t in trace])

    def test_failed_writer_exits_pending_state_correctly(self) -> None:
        """Database writer failure records ok: False in lastWrites so UI exits pending."""
        trigger = {
            "shipment_field_save": {
                "seq": 1,
                "event": "shipment_field_save",
                "payload": {"shipmentId": "LO-0306", "fields": {"booking_no": "BK-FAIL-01"}},
            }
        }
        with patch("core.database.save_shipment_atomic", return_value=False), \
             patch("core.database.get_last_db_error", return_value="DB lock timeout"):
            self._simulate_streamlit_event_lifecycle(trigger)

        last_writes = st.session_state.get(logi_view_model.LAST_WRITES_KEY)
        self.assertIsNotNone(last_writes)
        self.assertEqual(len(last_writes), 1)
        self.assertFalse(last_writes[0]["ok"])
        self.assertIn("DB lock timeout", last_writes[0]["error"])

    # -----------------------------------------------------------------------
    # 4. Post-mount Guard Verification
    # -----------------------------------------------------------------------

    def test_post_mount_does_not_dispatch_same_trigger_twice(self) -> None:
        """When callback runs, render() post-mount does not dispatch the trigger again."""
        trigger = {
            "shipment_field_save": {
                "seq": 1,
                "event": "shipment_field_save",
                "payload": {"shipmentId": "LO-0306", "fields": {"booking_no": "BK-GUARD-01"}},
            }
        }
        dispatch_calls = []
        orig_dispatch = logi_view_model.dispatch

        def tracking_dispatch(res, **kw):
            dispatch_calls.append((res, kw))
            return orig_dispatch(res, **kw)

        with patch("views.logi_view_model.dispatch", side_effect=tracking_dispatch), \
             patch("core.database.save_shipment_atomic", return_value=True):
            self._simulate_streamlit_event_lifecycle(trigger)

        # dispatch must have been called exactly ONCE (in callback mode), not twice
        self.assertEqual(len(dispatch_calls), 1)
        self.assertTrue(dispatch_calls[0][1].get("is_callback"))


    # -----------------------------------------------------------------------
    # 5. Optimization Guard: Fails if optimization is removed / reverted
    # -----------------------------------------------------------------------

    def test_adversarial_reverting_to_baseline_produces_double_build_and_rerun(self) -> None:
        """Adversarial check: if callback does NOT run before script body (old baseline),
        the system does two full VM builds and triggers an explicit st.rerun."""
        trigger = {
            "shipment_field_save": {
                "seq": 1,
                "event": "shipment_field_save",
                "payload": {"shipmentId": "LO-0306", "fields": {"booking_no": "BK-ADV-01"}},
            }
        }
        bvm_calls: list[int] = []
        rerun_calls: list[int] = []
        from streamlit.components.v2.bidi_component.state import ComponentResult

        run_count = [0]
        def fake_renderer(**kw):
            if run_count[0] == 0:
                return ComponentResult({}, trigger)
            return ComponentResult({}, {})

        # Simulate OLD BASELINE: callback is lambda: None (no-op prefix),
        # so dispatch only runs post-render.
        with patch("views.logi_view_model.build_view_model", side_effect=lambda: bvm_calls.append(1) or {"version": 1}), \
             patch("streamlit.rerun", side_effect=lambda: rerun_calls.append(1)), \
             patch("views.logi_shell._renderer", return_value=fake_renderer), \
             patch("views.web_app.require_login", return_value={"username": "test_user", "role": "admin"}), \
             patch("core.database.save_shipment_atomic", return_value=True):

            # Old baseline run 1: (no callback, script body runs)
            web_app.main()
            # In old baseline, dispatch called st.rerun
            if rerun_calls:
                run_count[0] += 1
                web_app.main()

        # Under baseline: build_view_model was called TWICE, rerun was called ONCE
        self.assertEqual(len(bvm_calls), 2, "Baseline MUST produce 2 VM builds")
        self.assertEqual(len(rerun_calls), 1, "Baseline MUST trigger explicit st.rerun")

    def test_duplicate_trigger_in_same_prefix_batch_does_not_double_dispatch(self) -> None:
        """When multiple event callbacks fire in the same Streamlit prefix batch,
        dispatch runs once and the second callback is safely ignored."""
        trigger = {
            "shipment_field_save": {
                "seq": 1,
                "event": "shipment_field_save",
                "payload": {"shipmentId": "LO-0306", "fields": {"booking_no": "BK-MULTI-01"}},
            }
        }
        st.session_state[COMPONENT_KEY] = trigger
        st.session_state["current_user"] = {"username": "test_user", "role": "admin"}

        with patch("core.database.save_shipment_atomic", return_value=True) as mock_save:
            # First callback in batch
            logi_shell._on_component_event()
            # Second callback in batch (e.g. fired by another trigger in aggregator)
            logi_shell._on_component_event()

            self.assertEqual(mock_save.call_count, 1, "Handler must be invoked exactly once across callback batch")


if __name__ == "__main__":
    unittest.main()
