#!/usr/bin/env python3
"""Generate the consolidation DOM-acceptance fixture from the REAL backend.

``LOGI_GOOD_FRONTEND_CONSOLIDATION_01`` walks EVERY visible destination in the
shell, so it needs the complete current view-model — the old Phase B fixture
predates the C1 commercial projections (quotes without service lines crash
the real Sales/Agreements/Contracts pages). This script:

  1. boots the isolated staging transport (mongomock — never production),
  2. seeds the standard staging workspace (same data an empty-staging
     Preview shows),
  3. dumps the real ``build_view_model()`` payload verbatim.

Run:  python scripts/gen_consolidation_fixture.py
Out:  tests/component/fixtures/view_model_consolidation.json
"""

from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

OUT = ROOT / "tests" / "component" / "fixtures" / "view_model_consolidation.json"


def main() -> None:
    import streamlit as st

    from views import logi_sandbox
    from views import logi_view_model as vm

    logi_sandbox.reset_backend()
    transport = logi_sandbox.ensure_backend()
    assert transport == logi_sandbox.SANDBOX_TRANSPORT, "this fixture must not touch production"
    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)

    model = vm.build_view_model()

    payload = {
        "generatedFrom": "scripts/gen_consolidation_fixture.py — isolated mongomock staging",
        **model,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1, default=str), encoding="utf-8")

    print(f"wrote {OUT}")
    print(f"  shipments={len(model['shipments'])} tasks={len(model['tasks'])} "
          f"customers={len(model['customers'])} quotes={len(model['quotes'])} "
          f"agreements={len(model['agreements'])} contracts={len(model['contracts'])} "
          f"receivables={len(model['receivables']['rows'])} payables={len(model['payables']['rows'])} "
          f"notifications={len(model['notifications'])}")
    open_tasks = sum(1 for t in model["tasks"] if t["level"] in ("Khan", "CanXuLy"))
    print(f"  open tasks (Khan+CanXuLy)={open_tasks}  env={model['environment']['transport']}")
    undated = [s["id"] for s in model["shipments"] if not (s.get("pxk") or {}).get("done") and not (s.get("pxk") or {}).get("date")]
    print(f"  shipments with PXK not done & no PXK date: {undated}")


if __name__ == "__main__":
    main()
