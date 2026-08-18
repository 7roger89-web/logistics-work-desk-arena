"""Read-only probe of production logistics_db: users collection + counts.

Reads the connection string from .streamlit/secrets.toml in the repo root
(if the owner's secrets were committed locally). Fails safely without writing.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

SECRETS = REPO / ".streamlit" / "secrets.toml"

if SECRETS.exists():
    try:
        import toml  # noqa: PLC0415

        cfg = toml.load(SECRETS)
        mongo = cfg.get("mongo", {})
        uri = mongo.get("uri", "")
        db_name = mongo.get("database", "logistics_db")
    except Exception as exc:  # noqa: BLE001
        print(f"SECRETS_UNREADABLE: {exc}")
        sys.exit(1)
else:
    print("SECRETS_MISSING: .streamlit/secrets.toml not found in repo root")
    sys.exit(1)

if not uri.startswith("mongodb"):
    print(f"URI_INVALID: starts with {uri[:15]!r}")
    sys.exit(1)

from pymongo import MongoClient  # noqa: PLC0415

client = MongoClient(uri, serverSelectionTimeoutMS=15000)
server = client.server_info()
print(f"SERVER_OK: MongoDB {server.get('version')}")

db = client.get_database(db_name)
print(f"DATABASE: {db.name}")

cols = db.list_collection_names()
print(f"COLLECTIONS({len(cols)}): {sorted(cols)}")

users = db.get_collection("users")
user_count = users.count_documents({})
print(f"USERS_COLLECTION: exists=True, count={user_count}")
for doc in users.find().limit(5):
    safe = {k: (v if k in {"username", "display_name", "role", "active"} else "***")
            for k, v in doc.items()}
    print("  SAMPLE:", safe)

# Compare with pre-cutover inventory
print("CUTOVER_REFERENCE: customers/shipments/audit_logs counts pre-cutover were 362/78/54")
print("DONE")
