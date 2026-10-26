"""Kiểm tra launcher và toàn bộ route đang ship mà không render giao diện.

Từ PR #44 app chỉ còn MỘT shell React, nên bảng route duy nhất là
``component/src/App.tsx``; ``views/web_app.py`` chỉ còn là launcher và không
còn ``ROUTES`` Streamlit nào (``ROUTER_HOTFIX.md`` là hồ sơ lịch sử). Script
đọc thẳng bảng route đang ship đó — không dựng registry thứ hai — và kiểm tra:

* mỗi ``<Route>`` trỏ tới một page component có thật và đã được import;
* mỗi redirect ``<Navigate to=...>`` trỏ tới một route đã khai báo;
* ``app.py`` / ``web_app.py`` gọi ``views.web_app.main``;
* phía Python của mọi route — ``views.web_app.main`` và dispatcher một cửa
  ``views.logi_view_model`` — import được và callable.
"""
from __future__ import annotations

import importlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

APP_TSX = ROOT / "component" / "src" / "App.tsx"
PAGES_DIR = ROOT / "component" / "src" / "pages"
LAUNCHERS = (ROOT / "app.py", ROOT / "web_app.py")

_ROUTE = re.compile(r'<Route\s+path="([^"]+)"\s+element=\{\s*<([A-Za-z_]\w*)([^>]*?)/>\s*\}\s*/>')
_PAGE_IMPORT = re.compile(r'^import\s+([A-Za-z_]\w*)\s+from\s+"\./pages/([^"]+)"', re.MULTILINE)
_REDIRECT = re.compile(r'\bto="([^"]+)"')


def run() -> int:
    failures: list[str] = []

    source = APP_TSX.read_text(encoding="utf-8")
    routes = _ROUTE.findall(source)
    declared = {path for path, _, _ in routes}
    page_imports = {name: target for name, target in _PAGE_IMPORT.findall(source)}

    if not routes:
        failures.append(f"{APP_TSX.name}: không tìm thấy <Route> nào")
        print(f"ERR {failures[-1]}")

    for path, element, attrs in routes:
        if element == "Navigate":
            target = _REDIRECT.search(attrs)
            if target is None or target.group(1) not in declared:
                wanted = target.group(1) if target else "?"
                failures.append(f"{path}: redirect tới route không khai báo ({wanted})")
                print(f"ERR {failures[-1]}")
            else:
                print(f"OK  {path}: redirect → {target.group(1)}")
            continue

        page = PAGES_DIR / f"{page_imports.get(element, '')}.tsx"
        if element not in page_imports or not page.exists():
            failures.append(f"{path}: page {element} chưa import hoặc không có file")
            print(f"ERR {failures[-1]}")
        else:
            print(f"OK  {path}: {element}")

    for launcher in LAUNCHERS:
        text = launcher.read_text(encoding="utf-8")
        if "from views.web_app import main" not in text or "main()" not in text:
            failures.append(f"{launcher.name}: không gọi views.web_app.main()")
            print(f"ERR {failures[-1]}")
        else:
            print(f"OK  launcher: {launcher.name} → views.web_app.main()")

    try:
        web_app = importlib.import_module("views.web_app")
        if not callable(getattr(web_app, "main", None)):
            raise TypeError("main không callable")
        print("OK  shell: views.web_app.main")
    except Exception as exc:  # noqa: BLE001 - báo đúng lỗi thật của launcher
        failures.append(f"views.web_app: {type(exc).__name__}: {exc}")
        print(f"ERR {failures[-1]}")

    try:
        view_model = importlib.import_module("views.logi_view_model")
        for name in ("build_view_model", "dispatch"):
            if not callable(getattr(view_model, name, None)):
                raise TypeError(f"{name} không callable")
        if not getattr(view_model, "ALL_EVENTS", None):
            raise TypeError("ALL_EVENTS rỗng")
        print("OK  dispatcher: views.logi_view_model.build_view_model/dispatch")
    except Exception as exc:  # noqa: BLE001 - báo đúng lỗi thật của dispatcher
        failures.append(f"views.logi_view_model: {type(exc).__name__}: {exc}")
        print(f"ERR {failures[-1]}")

    if failures:
        print("\nROUTER CHECK FAILED")
        for item in failures:
            print(f"- {item}")
        return 1
    print("\nROUTER CHECK PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
