"""Kiểm tra launcher và tất cả route mà không render giao diện."""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from views.web_app import ROUTES  # noqa: E402


def run() -> int:
    failures: list[str] = []
    for route in ROUTES:
        try:
            module = importlib.import_module(route.module)
            view = getattr(module, route.function)
            if not callable(view):
                raise TypeError(f"{route.function} không callable")
            print(f"OK  {route.label}: {route.module}.{route.function}")
        except Exception as exc:
            failures.append(f"{route.label}: {type(exc).__name__}: {exc}")
            print(f"ERR {failures[-1]}")

    for launcher in (ROOT / "app.py", ROOT / "web_app.py"):
        text = launcher.read_text(encoding="utf-8")
        if "main()" not in text:
            failures.append(f"{launcher.name}: thiếu main()")
        else:
            print(f"OK  launcher: {launcher.name}")

    if failures:
        print("\nROUTER CHECK FAILED")
        for item in failures:
            print(f"- {item}")
        return 1
    print("\nROUTER CHECK PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
