#!/usr/bin/env python3
"""Generate the LOGI_NOTEBOOK_WORKSPACE_01 DOM-acceptance fixture.

The fixture comes from the real, isolated mongomock staging view-model — never
from hand-written browser data and never from production. It captures:

* ``empty``: the staging deployment as it is, with no team note in the database.
  The handbook must render its static reference rows and describe the notes
  section as empty (no fabricated article);
* ``journey``: two notes written through the EXISTING canonical notebook writer
  (``core.database.save_knowledge_entry``), so note text, recorded date,
  category and tags are proven to reach the React page with their own
  provenance.

Run:  .venv/bin/python scripts/gen_handbook_fixture.py
Out:  tests/component/fixtures/view_model_handbook.json
"""

from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
OUT = ROOT / "tests" / "component" / "fixtures" / "view_model_handbook.json"

NOTES = (
    {
        "id": "HB-FIX-DOC-1",
        "title": "Hàng nhập cần bill gốc trước khi giao",
        "category": "📄 Chứng Từ (Docs)",
        "content": "Khách yêu cầu bản gốc tại cảng; chỉ nhận bản fax khi đã có email xác nhận.",
        "tags": ["bill gốc", "giao hàng"],
        "date": "04/09/2026 09:12",
    },
    {
        "id": "HB-FIX-CUSTOMS-1",
        "title": "Luồng vàng: chuẩn bị hồ sơ bổ sung trước 24h",
        "category": "🏛️ Hải Quan",
        "content": "Khi có kết quả phân luồng vàng, báo khách và chuẩn bị hồ sơ bổ sung trong ngày.",
        "tags": ["phân luồng", "hải quan"],
        "date": "06/09/2026 15:40",
    },
)


def main() -> None:
    import streamlit as st

    from core.database import save_knowledge_entry
    from views import logi_sandbox
    from views import logi_view_model as vm

    logi_sandbox.reset_backend()
    transport = logi_sandbox.ensure_backend()
    assert transport == logi_sandbox.SANDBOX_TRANSPORT, "fixture must not touch production"
    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)

    empty = vm.build_view_model()
    empty_notes = empty["handbook"]["sections"][-1]
    assert empty["handbook"]["readOnly"] is True
    assert empty_notes["id"] == "ghi-chu"
    assert empty_notes["entries"] == [] and empty_notes["state"] is not None

    for note in NOTES:
        assert save_knowledge_entry(dict(note)), "staging note write failed"

    journey = vm.build_view_model()
    section = next(s for s in journey["handbook"]["sections"] if s["id"] == "ghi-chu")
    assert len(section["entries"]) == len(NOTES)
    assert all(entry["provenance"]["updated"] for entry in section["entries"])
    assert "Ghi chú đội ngũ" in journey["handbook"]["sectionsAvailable"]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(
            {
                "generatedFrom": "scripts/gen_handbook_fixture.py — isolated mongomock staging",
                "empty": empty,
                "journey": journey,
            },
            ensure_ascii=False,
            indent=1,
            default=str,
        ),
        encoding="utf-8",
    )

    handbook = journey["handbook"]
    print(f"wrote {OUT.relative_to(ROOT)}")
    print(
        "  empty: "
        f"sections={empty['handbook']['counts']['availableSectionCount']}/"
        f"{empty['handbook']['counts']['sectionCount']} "
        f"entries={empty['handbook']['counts']['entryCount']} "
        f"notes={empty['handbook']['counts']['noteCount']}"
    )
    print(
        "  journey: "
        f"entries={handbook['counts']['entryCount']} "
        f"notes={handbook['counts']['noteCount']} "
        f"noteTitles={[entry['title'] for entry in section['entries']]}"
    )

    logi_sandbox.reset_backend()


if __name__ == "__main__":
    main()
