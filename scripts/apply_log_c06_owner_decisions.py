"""Apply the confirmed LOG-C06 Owner decisions to staging only.

The explicit ``--apply`` flag is required so a caller cannot accidentally
turn a report/preview invocation into a staging write.  This script never
touches the canonical financial ledger.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.database import get_db
from core.historical_owner_decisions import OWNER_ACTOR, apply_owner_decisions


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply LOG-C06 Owner decisions to staging review only.")
    parser.add_argument("--apply", action="store_true", help="perform the audited staging-only batch")
    parser.add_argument("--actor", default=OWNER_ACTOR)
    parser.add_argument("--source-file-hash", default=None)
    parser.add_argument("--acted-at", default=None)
    args = parser.parse_args()
    if not args.apply:
        parser.error("--apply is required; this command is staging-only but still performs a durable metadata write")
    db = get_db()
    if db is None:
        raise RuntimeError("Staging database is unavailable; no action was performed.")
    result = apply_owner_decisions(
        db,
        actor=args.actor,
        source_file_hash=args.source_file_hash,
        acted_at=args.acted_at,
    )
    print(json.dumps(result, ensure_ascii=True, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
