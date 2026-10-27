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

        user_doc = {
            "username": "test_user",
            "display_name": "Test User",
            "role": auth_role,
            "active": True,
            "user_id": "u_test",
        }
        users_db = {"test_user": user_doc}
        from core import auth

        with patch("views.logi_view_model.build_view_model", side_effect=tracked_bvm), \
             patch("streamlit.rerun", side_effect=tracked_rerun), \
             patch("views.logi_shell._renderer", return_value=lambda **kw: renderer_return), \
             patch("views.web_app.require_login", return_value={"username": "test_user", "role": auth_role}), \
             patch.object(auth, "AUTH_REQUIRED", True), \
             patch("core.database.load_users", return_value=users_db):

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

    def test_contract_create_handler_and_vm_once(self) -> None:
        from views import logi_c1
        from core import database as db
        trigger = {"contract_create": {"seq": 1, "event": "contract_create",
                   "payload": {"id": "05/2026/HDMB", "customerId": "CUST-ANPHAT",
                               "requestId": "REQ-CONTRACT-ONCE"}}}
        with patch.dict(logi_c1._HANDLERS, {"contract_create": MagicMock(wraps=logi_c1._handle_contract_create)}), \
             patch.object(db, "save_contract_to_cloud", wraps=db.save_contract_to_cloud) as writer:
            handler = logi_c1._HANDLERS["contract_create"]
            trace = self._simulate_streamlit_event_lifecycle(trigger)
            self.assertEqual(handler.call_count, 1)
            self.assertEqual(writer.call_count, 1)
        self.assertEqual(sum(t[0] == "build_view_model" for t in trace), 1)
        self.assertNotIn("st.rerun", [t[0] for t in trace])
        outcome = st.session_state[logi_view_model.LAST_WRITES_KEY][0]
        self.assertTrue(outcome["ok"], outcome)
        self.assertEqual(outcome["requestId"], "REQ-CONTRACT-ONCE")
        self.assertEqual(outcome["readback"]["id"], "05/2026/HDMB")

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

        from core import auth

        # The post-mount fallback this simulated old baseline relies on
        # (views.logi_shell.render) also gates dispatch on a REVALIDATED
        # session via fresh_session_identity_for_action(), exactly like the
        # real app where require_login() has already run before the script
        # body. Without a canonical identity the fallback never dispatches and
        # this test would measure 1 VM build / 0 reruns instead of the baseline
        # double-build behaviour it asserts. This is a revalidation boundary,
        # not a production defect.
        users_db = {"test_user": {"username": "test_user", "display_name": "Test User",
                                  "role": "admin", "active": True, "user_id": "u_test"}}
        st.session_state["current_user"] = dict(users_db["test_user"])

        # Simulate OLD BASELINE: callback is lambda: None (no-op prefix),
        # so dispatch only runs post-render.
        with patch.object(auth, "AUTH_REQUIRED", True), \
             patch("core.database.load_users", return_value=users_db), \
             patch("views.logi_view_model.build_view_model", side_effect=lambda: bvm_calls.append(1) or {"version": 1}), \
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
        from core import auth

        # _on_component_event() revalidates the session against the canonical
        # user store (fresh_session_identity_for_action) BEFORE dispatching.
        # Without a canonical identity the handler is never invoked and this
        # test would measure 0 calls instead of exercising the batch guard.
        users_db = {"test_user": {"username": "test_user", "display_name": "Test User",
                                  "role": "admin", "active": True, "user_id": "u_test"}}
        st.session_state[COMPONENT_KEY] = trigger
        st.session_state["current_user"] = dict(users_db["test_user"])

        with patch.object(auth, "AUTH_REQUIRED", True), \
             patch("core.database.load_users", return_value=users_db), \
             patch("views.logi_view_model.dispatch", wraps=logi_view_model.dispatch) as mock_dispatch, \
             patch("core.database.save_shipment_atomic", return_value=True) as mock_save:
            # First callback in batch
            logi_shell._on_component_event()
            # Second callback in batch (e.g. fired by another trigger in aggregator)
            logi_shell._on_component_event()

            self.assertEqual(mock_save.call_count, 1, "Handler must be invoked exactly once across callback batch")
            # The seq-replay guard inside dispatch() would mask a second writer
            # call on its own, so also assert on the dispatcher: the
            # CALLBACK_DISPATCHED_FLAG guard must stop the second callback
            # BEFORE dispatch runs, not merely before the writer runs.
            self.assertEqual(mock_dispatch.call_count, 1, "Dispatch must run once per callback batch")

    # -----------------------------------------------------------------------
    # CONTROL_TOWER_SECURITY_REPAIR_01: Canonical Auth Revalidation Regressions
    # -----------------------------------------------------------------------

    def test_regression_a_stale_role_downgrade_refuses_writer(self) -> None:
        """A. STALE ROLE DOWNGRADE:
        Session before callback: role=support
        Canonical load_users: same user now role=viewer
        Trigger: shipment_field_save
        Assert:
        - canonical revalidation happens before business permission decision;
        - save_shipment_atomic call count = 0;
        - no stale support authority is used;
        - session role becomes viewer if that is the existing auth behavior.
        """
        user_before = {"username": "op.support", "display_name": "Op Support", "role": "support", "user_id": "u1"}
        users_db = {"op.support": {"username": "op.support", "display_name": "Op Support", "role": "viewer", "active": True, "user_id": "u1"}}

        st.session_state["current_user"] = dict(user_before)
        trigger = {
            "shipment_field_save": {
                "seq": 1,
                "event": "shipment_field_save",
                "payload": {"shipmentId": "LO-0306", "fields": {"booking_no": "BK-ROLE-DOWNGRADE"}},
            }
        }
        st.session_state[COMPONENT_KEY] = trigger

        from core import auth
        with patch.object(auth, "AUTH_REQUIRED", True), \
             patch("core.database.load_users", return_value=users_db), \
             patch("core.database.save_shipment_atomic", return_value=True) as mock_save:
            logi_shell._on_component_event()

            self.assertEqual(mock_save.call_count, 0, "save_shipment_atomic must NOT be called when role is downgraded to viewer")
            self.assertEqual(st.session_state["current_user"]["role"], "viewer", "Session state role must be revalidated to viewer")
            last_writes = st.session_state.get(logi_view_model.LAST_WRITES_KEY, [])
            self.assertTrue(any(w.get("ok") is False and "shipment_edit" in w.get("error", "") for w in last_writes),
                            "Refusal must be recorded in LAST_WRITES")

    def test_regression_b_deactivated_account_refuses_callback_dispatch(self) -> None:
        """B. DEACTIVATED ACCOUNT:
        Session: active support/admin identity
        Canonical record: active=false
        Trigger: shipment_create or shipment_field_save
        Assert:
        - writer call count = 0;
        - current_user removed/invalidated;
        - callback does not dispatch using old role.
        """
        user_before = {"username": "op.support", "display_name": "Op Support", "role": "support", "user_id": "u1"}
        users_db = {"op.support": {"username": "op.support", "display_name": "Op Support", "role": "support", "active": False, "user_id": "u1"}}

        st.session_state["current_user"] = dict(user_before)
        trigger = {
            "shipment_create": {
                "seq": 1,
                "event": "shipment_create",
                "payload": {"service_type": "SEA_IMPORT", "customer": "KH-001"},
            }
        }
        st.session_state[COMPONENT_KEY] = trigger

        from core import auth
        with patch.object(auth, "AUTH_REQUIRED", True), \
             patch("core.database.load_users", return_value=users_db), \
             patch("core.database.save_shipment_atomic", return_value=True) as mock_save:
            logi_shell._on_component_event()

            self.assertEqual(mock_save.call_count, 0, "Writer must not be called when account is deactivated")
            self.assertNotIn("current_user", st.session_state, "current_user must be removed/invalidated")
            self.assertNotIn(logi_shell.CALLBACK_DISPATCHED_FLAG, st.session_state, "CALLBACK_DISPATCHED_FLAG must not be set on refusal")

    def test_regression_c_canonical_user_store_failure_fails_closed(self) -> None:
        """C. CANONICAL USER STORE FAILURE:
        load_users raises.
        Assert:
        - fail CLOSED;
        - writer/provider call count = 0.
        """
        user_before = {"username": "op.admin", "display_name": "Op Admin", "role": "admin", "user_id": "u1"}
        st.session_state["current_user"] = dict(user_before)
        trigger = {
            "shipment_create": {
                "seq": 1,
                "event": "shipment_create",
                "payload": {"service_type": "SEA_IMPORT", "customer": "KH-001"},
            }
        }
        st.session_state[COMPONENT_KEY] = trigger

        from core import auth
        with patch.object(auth, "AUTH_REQUIRED", True), \
             patch("core.database.load_users", side_effect=RuntimeError("Canonical user store network drop")), \
             patch("core.database.save_shipment_atomic", return_value=True) as mock_save:
            logi_shell._on_component_event()

            self.assertEqual(mock_save.call_count, 0, "Writer must not be called on user store failure (fail closed)")
            self.assertNotIn("current_user", st.session_state, "current_user must be purged on store failure")
            self.assertNotIn(logi_shell.CALLBACK_DISPATCHED_FLAG, st.session_state)

    def test_regression_d_valid_active_user_preserves_single_vm_build_invariants(self) -> None:
        """D. VALID ACTIVE USER:
        Canonical store confirms permitted role.
        Assert existing performance property still holds:
        handler calls = 1
        VM builds/event = 1
        explicit second st.rerun = 0
        """
        users_db = {"op.admin": {"username": "op.admin", "display_name": "Op Admin", "role": "admin", "active": True, "user_id": "u1"}}
        st.session_state["current_user"] = dict(users_db["op.admin"])

        trigger = {
            "shipment_field_save": {
                "seq": 1,
                "event": "shipment_field_save",
                "payload": {"shipmentId": "LO-0306", "fields": {"booking_no": "BK-VALID-01"}},
            }
        }
        st.session_state[COMPONENT_KEY] = trigger

        bvm_calls = []
        rerun_calls = []
        from streamlit.components.v2.bidi_component.state import ComponentResult
        from core import auth

        with patch.object(auth, "AUTH_REQUIRED", True), \
             patch("core.database.load_users", return_value=users_db), \
             patch("views.logi_view_model.build_view_model", side_effect=lambda: bvm_calls.append(1) or {}), \
             patch("streamlit.rerun", side_effect=lambda: rerun_calls.append(1)), \
             patch("views.logi_shell._renderer", return_value=lambda **kw: ComponentResult({}, trigger)), \
             patch("core.database.save_shipment_atomic", return_value=True) as mock_save:

            # Execute normal Streamlit lifecycle: prefix callback then script body
            logi_shell._on_component_event()
            web_app.main()

            self.assertEqual(mock_save.call_count, 1, "Handler must be called exactly once")
            self.assertEqual(len(bvm_calls), 1, "Exactly 1 VM build per event")
            self.assertEqual(len(rerun_calls), 0, "Zero explicit second st.rerun()")

    def test_regression_e_translation_auth_downgrade_refuses_provider_call(self) -> None:
        """E. TRANSLATION AUTH DOWNGRADE:
        Session role currently has translation permission.
        Canonical record changes to a role without translation.
        Trigger translate_text.
        Assert:
        run_translation call count = 0.
        This proves provider billing cannot occur under stale authority.
        """
        user_before = {"username": "op.sale", "display_name": "Op Sale", "role": "sale", "user_id": "u1"}
        users_db = {"op.sale": {"username": "op.sale", "display_name": "Op Sale", "role": "viewer", "active": True, "user_id": "u1"}}

        st.session_state["current_user"] = dict(user_before)
        trigger = {
            "translate_text": {
                "seq": 1,
                "event": "translate_text",
                "payload": {"text": "Bill of Lading", "sourceLang": "EN", "targetLang": "VI"},
            }
        }
        st.session_state[COMPONENT_KEY] = trigger

        from core import auth
        with patch.object(auth, "AUTH_REQUIRED", True), \
             patch("core.database.load_users", return_value=users_db), \
             patch("views.translation.run_translation") as mock_translate:
            logi_shell._on_component_event()

            self.assertEqual(mock_translate.call_count, 0, "run_translation provider must NOT be called after role downgrade")
            self.assertEqual(st.session_state["current_user"]["role"], "viewer")

    def test_regression_f_callback_flag_recovery_after_auth_refusal(self) -> None:
        """F. CALLBACK FLAG RECOVERY:
        Auth refusal on one callback -> later valid authenticated event.
        Assert:
        second legitimate event is not swallowed by stale callback flag.
        """
        from streamlit.components.v2.bidi_component.state import ComponentResult
        from core import auth

        # 1. Event 1 arrives under deactivated identity
        users_db = {"op.support": {"username": "op.support", "display_name": "Op Support", "role": "support", "active": False, "user_id": "u1"}}
        st.session_state["current_user"] = {"username": "op.support", "display_name": "Op Support", "role": "support", "user_id": "u1"}
        trigger1 = {
            "shipment_field_save": {
                "seq": 1,
                "event": "shipment_field_save",
                "payload": {"shipmentId": "LO-0306", "fields": {"booking_no": "BK-EVT-1"}},
            }
        }
        st.session_state[COMPONENT_KEY] = trigger1

        with patch.object(auth, "AUTH_REQUIRED", True), \
             patch("core.database.load_users", return_value=users_db), \
             patch("core.database.save_shipment_atomic", return_value=True) as mock_save1:
            logi_shell._on_component_event()
            self.assertEqual(mock_save1.call_count, 0, "Event 1 writer must be refused")
            self.assertNotIn(logi_shell.CALLBACK_DISPATCHED_FLAG, st.session_state, "No lingering flag on refusal")

        # 2. Event 2 arrives under restored/valid identity
        users_db["op.support"]["active"] = True
        st.session_state["current_user"] = dict(users_db["op.support"])
        trigger2 = {
            "shipment_field_save": {
                "seq": 2,
                "event": "shipment_field_save",
                "payload": {"shipmentId": "LO-0306", "fields": {"booking_no": "BK-EVT-2"}},
            }
        }
        st.session_state[COMPONENT_KEY] = trigger2

        with patch.object(auth, "AUTH_REQUIRED", True), \
             patch("core.database.load_users", return_value=users_db), \
             patch("core.database.save_shipment_atomic", return_value=True) as mock_save2:
            logi_shell._on_component_event()
            self.assertEqual(mock_save2.call_count, 1, "Legitimate Event 2 must be dispatched and executed")
            self.assertTrue(st.session_state.get(logi_shell.CALLBACK_DISPATCHED_FLAG))

            # Simulate render consuming the callback flag
            with patch("views.logi_shell._renderer", return_value=lambda **kw: ComponentResult({}, trigger2)):
                logi_shell.render({})
            self.assertNotIn(logi_shell.CALLBACK_DISPATCHED_FLAG, st.session_state)
            self.assertEqual(mock_save2.call_count, 1, "Event 2 must not be double dispatched in render")

    def test_adversarial_bypassing_canonical_revalidation_allows_stale_role_write(self) -> None:
        """Adversarial check: proves that bypassing callback-time canonical revalidation
        would allow a downgraded session to execute forbidden writes under stale authority."""
        user_before = {"username": "op.support", "display_name": "Op Support", "role": "support", "user_id": "u1"}
        users_db = {"op.support": {"username": "op.support", "display_name": "Op Support", "role": "viewer", "active": True, "user_id": "u1"}}

        st.session_state["current_user"] = dict(user_before)
        trigger = {
            "shipment_field_save": {
                "seq": 1,
                "event": "shipment_field_save",
                "payload": {"shipmentId": "LO-0306", "fields": {"booking_no": "BK-ROLE-DOWNGRADE"}},
            }
        }
        st.session_state[COMPONENT_KEY] = trigger

        from core import auth
        # Simulate an insecure/bypassed callback that does not revalidate canonical store
        with patch.object(auth, "AUTH_REQUIRED", True), \
             patch("core.database.load_users", return_value=users_db), \
             patch("core.auth.fresh_session_identity_for_action", return_value=dict(user_before)), \
             patch("core.database.save_shipment_atomic", return_value=True) as mock_save:
            logi_shell._on_component_event()
            # Under bypass, the writer is vulnerably invoked with stale support authority:
            self.assertEqual(mock_save.call_count, 1, "Bypassing canonical revalidation allowed stale write")

        # Now verify that the REAL secure implementation properly blocks the write:
        st.session_state.pop(logi_shell.CALLBACK_DISPATCHED_FLAG, None)
        st.session_state["current_user"] = dict(user_before)
        trigger["shipment_field_save"]["seq"] = 2
        st.session_state[COMPONENT_KEY] = trigger
        with patch.object(auth, "AUTH_REQUIRED", True), \
             patch("core.database.load_users", return_value=users_db), \
             patch("core.database.save_shipment_atomic", return_value=True) as mock_save_real:
            logi_shell._on_component_event()
            self.assertEqual(mock_save_real.call_count, 0, "Secure callback strictly blocked stale write")
            self.assertEqual(st.session_state["current_user"]["role"], "viewer")

    def test_regression_auth_required_false_always_establishes_local_admin(self) -> None:
        """AUTH_REQUIRED=False + session initially contains viewer/support user
        -> fresh_session_identity_for_action() returns local-admin/admin
        -> session current_user becomes local-admin/admin.
        """
        from core import auth

        for stale_role in ("viewer", "support"):
            st.session_state["current_user"] = {
                "username": f"stale.{stale_role}",
                "display_name": f"Stale {stale_role.capitalize()}",
                "role": stale_role,
                "user_id": f"u_{stale_role}",
            }
            with patch.object(auth, "AUTH_REQUIRED", False):
                user = auth.fresh_session_identity_for_action()
                self.assertEqual(user["username"], "local-admin")
                self.assertEqual(user["role"], "admin")
                self.assertEqual(user["display_name"], "Local Admin")
                self.assertEqual(st.session_state["current_user"]["username"], "local-admin")
                self.assertEqual(st.session_state["current_user"]["role"], "admin")
                self.assertEqual(st.session_state["current_user"]["display_name"], "Local Admin")


if __name__ == "__main__":
    unittest.main()
