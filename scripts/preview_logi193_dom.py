#!/usr/bin/env python3
"""LOGI-193 — real-browser render harness for the Admin-uploaded Office templates.

The sandbox has no browser binary, so screenshots cannot be produced here. This
script instead serves the ACTUAL production bundle
(``component/dist/logi-shell.js``) together with the payload produced by the
real staging stack, so the surfaces can be inspected in a real browser at a
true 1440x900 and 390x844 viewport:

    .venv/bin/python scripts/gen_logi193_dom_fixture.py --fixture /tmp/logi193-dom.json
    .venv/bin/python scripts/preview_logi193_dom.py --fixture /tmp/logi193-dom.json --port 8600

Nothing here touches the database: the payload is read from the fixture file and
no event is dispatched anywhere. The viewport switch is a real viewport — the
component mounts inside an iframe whose width/height are set, not a container
whose width is merely constrained.
"""

from __future__ import annotations

import argparse
import mimetypes
import pathlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

ROOT = pathlib.Path(__file__).resolve().parents[1]
DIST = ROOT / "component" / "dist"

OUTER = """<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="utf-8">
<title>LOGI-193 — biểu mẫu Office do Admin tải lên</title>
<style>
  body {{ margin: 0; background: #0f172a; color: #e2e8f0;
         font: 13px/1.5 system-ui, sans-serif; }}
  header {{ padding: 10px 16px; display: flex; gap: 8px; align-items: center;
            flex-wrap: wrap; border-bottom: 1px solid #1e293b; }}
  button {{ background: #1e293b; color: #e2e8f0; border: 1px solid #334155;
            border-radius: 6px; padding: 6px 12px; cursor: pointer; font: inherit; }}
  button[aria-pressed="true"] {{ background: #2563eb; border-color: #3b82f6; }}
  main {{ padding: 16px; }}
  iframe {{ border: 1px solid #334155; background: #fff; display: block; }}
  .note {{ color: #94a3b8; }}
</style>
</head>
<body>
<header>
  <strong>LOGI-193</strong>
  <button data-w="1440" data-h="900" aria-pressed="true">Desktop 1440x900</button>
  <button data-w="390" data-h="844" aria-pressed="false">Mobile 390x844</button>
  <span class="note" id="vp">1440 x 900</span>
  <span class="note">— khung nhìn thật (iframe), bundle production, dữ liệu từ staging</span>
</header>
<main><iframe id="frame" src="/shell" width="1440" height="900"></iframe></main>
<script>
  const frame = document.getElementById('frame');
  const vp = document.getElementById('vp');
  for (const button of document.querySelectorAll('button[data-w]')) {{
    button.addEventListener('click', () => {{
      for (const other of document.querySelectorAll('button[data-w]'))
        other.setAttribute('aria-pressed', String(other === button));
      frame.width = button.dataset.w;
      frame.height = button.dataset.h;
      vp.textContent = button.dataset.w + ' x ' + button.dataset.h;
    }});
  }}
</script>
</body>
</html>
"""

INNER = """<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>LOGI-193 shell</title>
<link rel="stylesheet" href="/dist/logi-shell.css">
</head>
<body>
<div id="root"></div>
<script type="module">
  import mount from '/dist/logi-shell.js';
  const payload = await (await fetch('/fixture.json')).json();
  const model = payload.viewModel;
  model.shipmentDocumentPicker = payload.picker;
  model.docgenTemplates = payload.workspace;
  window.__logi193Triggers = [];
  const cleanup = mount({
    name: 'logi_shell',
    data: model,
    parentElement: document.getElementById('root'),
    setTriggerValue: (event, value) => window.__logi193Triggers.push({ event, value }),
  });
  window.__logi193Cleanup = cleanup;
  window.__logi193Reload = async () => {
    if (typeof cleanup === 'function') cleanup();
    const fresh = await (await fetch('/fixture.json')).json();
    const next = fresh.viewModel;
    next.shipmentDocumentPicker = fresh.picker;
    next.docgenTemplates = fresh.workspace;
    mount({
      name: 'logi_shell',
      data: next,
      parentElement: document.getElementById('root'),
      setTriggerValue: (event, value) => window.__logi193Triggers.push({ event, value }),
    });
  };
</script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    fixture_path = DIST  # replaced in main()

    def _send(self, body: bytes, content_type: str, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        route = urlparse(self.path).path
        if route in ("/", "/index.html"):
            self._send(OUTER.encode(), "text/html; charset=utf-8")
            return
        if route == "/shell":
            self._send(INNER.encode(), "text/html; charset=utf-8")
            return
        if route == "/fixture.json":
            if not self.fixture_path.exists():
                self._send(b'{"error":"fixture missing"}', "application/json", 404)
                return
            self._send(self.fixture_path.read_bytes(), "application/json")
            return
        if route.startswith("/dist/"):
            target = (DIST / route[len("/dist/"):]).resolve()
            if not str(target).startswith(str(DIST.resolve())) or not target.is_file():
                self._send(b"not found", "text/plain", 404)
                return
            kind = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
            if target.suffix == ".js":
                kind = "text/javascript"
            self._send(target.read_bytes(), kind)
            return
        self._send(b"not found", "text/plain", 404)

    def log_message(self, *_args) -> None:  # keep the preview log quiet
        return


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", default="/tmp/logi193-dom.json")
    parser.add_argument("--port", type=int, default=8600)
    parser.add_argument("--host", default="0.0.0.0")
    args = parser.parse_args()

    Handler.fixture_path = pathlib.Path(args.fixture)
    if not Handler.fixture_path.exists():
        raise SystemExit(
            f"fixture not found: {args.fixture}\n"
            "run: .venv/bin/python scripts/gen_logi193_dom_fixture.py "
            f"--fixture {args.fixture}"
        )
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"LOGI-193 render harness on http://{args.host}:{args.port}")
    print(f"  fixture: {args.fixture}")
    print(f"  bundle : {DIST / 'logi-shell.js'}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
