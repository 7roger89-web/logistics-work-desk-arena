"""Reusable local UI smoke check for the LOG-C06 Historical Review surface."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from streamlit.testing.v1 import AppTest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def main() -> int:
    app = AppTest.from_file(str(PROJECT_ROOT / "app.py"))
    app.session_state["active_page"] = "Công nợ A Bò"
    app.session_state["log_c05_partner_view"] = "historical_review"
    app.run(timeout=120)
    errors = [element.value for element in app.exception]
    texts = [element.value for element in app.markdown] + [element.value for element in app.caption]
    all_text = " ".join(texts)
    result = {
        "exception_count": len(errors),
        "exceptions": errors[:5],
        "has_six_source_status": "Six-source status" in all_text,
        "has_reconciled_label": "RECONCILED" in all_text,
        "has_received_total": "416,482" in all_text,
        "dataframe_count": len(app.dataframe),
        "dataframe_shapes": [getattr(element.value, "shape", None) for element in app.dataframe],
    }
    print(json.dumps(result, ensure_ascii=True, default=str))
    return 0 if not errors and result["has_six_source_status"] and result["has_reconciled_label"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
