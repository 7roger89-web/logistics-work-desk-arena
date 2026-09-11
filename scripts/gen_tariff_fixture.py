#!/usr/bin/env python3
"""Generate the LOGI_TARIFF_LOOKUP_01 DOM-acceptance fixture.

Same contract as gen_consolidation_fixture.py: boot the ISOLATED mongomock
staging transport (never production), dump the real ``build_view_model()``
payload verbatim. This generator additionally:

  1. creates a tiny canonical-schema reference database (3 rows, no rates —
     the sanitized schema carries no duty/VAT columns) and points
     ``core.utils.TARIFF_DB_PATH`` at it for the dump only,
  2. records a submitted lookup query so the fixture carries the REAL reader
     result for that query (exactly what the live rerun would deliver).

Run:  python scripts/gen_tariff_fixture.py
Out:  tests/component/fixtures/view_model_tariff.json
"""
from __future__ import annotations

import json
import pathlib
import sqlite3
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

OUT = ROOT / "tests" / "component" / "fixtures" / "view_model_tariff.json"

ROWS = [
    ("9401.61.00", "Ghế ngồi có lưng, khung bằng gỗ", "Seats with wooden frames"),
    ("9403.20.10", "Bàn kim loại cho văn phòng", "Metal office tables"),
    ("4418.10.00", "Cửa sổ, cửa đi bằng gỗ", "Wooden windows and doors"),
]


def main() -> None:
    import streamlit as st

    from views import logi_sandbox
    from views import logi_view_model as vm

    logi_sandbox.reset_backend()
    transport = logi_sandbox.ensure_backend()
    assert transport == logi_sandbox.SANDBOX_TRANSPORT, "this fixture must not touch production"
    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)

    with tempfile.TemporaryDirectory() as tmp:
        db = pathlib.Path(tmp) / "tariff.db"
        with sqlite3.connect(str(db)) as conn:
            conn.execute(
                'CREATE TABLE tariff_table ("Mã HS" TEXT, "Mô tả tiếng Việt" TEXT,'
                ' "Mô tả tiếng Anh" TEXT)'
            )
            conn.executemany("INSERT INTO tariff_table VALUES (?,?,?)", ROWS)
        import core.utils
        real_path = core.utils.TARIFF_DB_PATH
        core.utils.TARIFF_DB_PATH = db
        try:
            st.session_state[vm.TARIFF_QUERY_KEY] = "9401"
            model = vm.build_view_model()
        finally:
            core.utils.TARIFF_DB_PATH = real_path

    payload = {
        "generatedFrom": "scripts/gen_tariff_fixture.py — isolated mongomock staging",
        **model,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    tariff = model["tariff"]
    print(f"wrote {OUT}")
    print(f"  tariff: searched={tariff['searched']} count={tariff['count']} "
          f"first={tariff['rows'][0]['hsCode'] if tariff['rows'] else None} "
          f"source.configured={tariff['source']['configured']}")


if __name__ == "__main__":
    main()
