#!/usr/bin/env python3
"""Run the isolated HEXA V0 Trial Portal HTTP server (bound to 0.0.0.0:8787 by default)."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.hexa_trial_portal import (  # noqa: E402
    create_trial_http_server,
    get_trial_environment,
    seed_live_preview_publications,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="HEXA V0 TT -> LG Trial Portal HTTP Server")
    parser.add_argument("--host", default="0.0.0.0", help="Bind host (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8787, help="Bind port (default: 8787)")
    parser.add_argument(
        "--internal-qa-mode",
        action="store_true",
        help="Enable isolated /internal/qa/* endpoints (still requires server-only X-Hexa-Internal-QA-Key)",
    )
    parser.add_argument(
        "--no-seed-published",
        action="store_true",
        help="Start with 0 published shipments (default pre-publishes ROAD-LG-001 and ROAD-MD-002 for Live Preview)",
    )
    args = parser.parse_args()

    env = get_trial_environment()
    if not args.no_seed_published:
        seed_live_preview_publications(env)
    server = create_trial_http_server(
        host=args.host,
        port=args.port,
        env=env,
        internal_qa_mode=bool(args.internal_qa_mode),
    )
    bound_host, bound_port = server.server_address[:2]
    print(
        f"HEXA_TRIAL_PORTAL_READY http://{bound_host}:{bound_port}/ "
        f"(isolated SANDBOX_STAGING: mongomock + GridFS, internal_qa_mode={bool(args.internal_qa_mode)})",
        flush=True,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
