#!/usr/bin/env python3
"""Generate the client-side execution-profile catalog from the ONE authority.

LOGI_SHIPMENT_EXECUTION_PROFILE_01 — the component applies conditional rules
*many times per operator click* (filtering the Incoterm list by version and mode,
switching the load-model family, deciding whether a truck or a container preset
is even relevant). A Streamlit rerun per keystroke would be absurd, so the small
matrices must exist in the browser too.

They are NOT re-typed by hand: this script emits exactly
``core.shipment_execution_profile.projection_options()`` into
``component/src/lib/executionProfileCatalog.ts``, and
``tests/test_logi_shipment_execution_profile_01.py`` fails if the committed file
ever drifts from the Python authority.

Run: python3 scripts/gen_execution_profile_catalog.py
"""

from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

OUT = ROOT / "component" / "src" / "lib" / "executionProfileCatalog.ts"

HEADER = """// ============================================================================
// GENERATED FILE — DO NOT EDIT BY HAND.
//
// Source of truth: core/shipment_execution_profile.py::projection_options()
// Regenerate with:  python3 scripts/gen_execution_profile_catalog.py
//
// The component needs these matrices locally (it filters the Incoterm list on
// every keystroke); the payload below is byte-identical to the Python
// authority, and the Python test suite fails if this file drifts from it.
// ============================================================================

"""


def render() -> str:
    from core.shipment_execution_profile import projection_options

    payload = json.dumps(projection_options(), ensure_ascii=False, indent=2, sort_keys=False)
    return (
        HEADER
        + "export const EXECUTION_PROFILE_CATALOG = "
        + payload
        + " as const;\n\n"
        + "export type ExecutionProfileCatalog = typeof EXECUTION_PROFILE_CATALOG;\n"
    )


def main() -> None:
    content = render()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(content, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} ({len(content)} bytes)")


if __name__ == "__main__":
    main()
