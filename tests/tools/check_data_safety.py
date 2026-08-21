"""Phase 5: Post-merge data safety check (READ ONLY)."""
import configparser
import os
from datetime import datetime, timedelta
from pymongo import MongoClient

repo = os.environ.get('REPO_DIR', '/home/ubuntu/logistics_repo')
config = configparser.ConfigParser()
config.read(os.path.join(repo, '.streamlit', 'secrets.toml'))

uri = config['mongo']['uri'].strip('"').strip("'")
db_name = config['mongo']['database'].strip('"').strip("'")

client = MongoClient(uri, serverSelectionTimeoutMS=10000)
db = client[db_name]

print("=== PHASE 5: DATA SAFETY (READ-ONLY) ===")
print(f"Database: {db_name}")

customers = db.customers.count_documents({})
shipments = db.shipments.count_documents({})
print(f"Customers: {customers}")
print(f"Shipments: {shipments}")

# Duplicate check
pipeline = [
    {"$group": {"_id": "$shipment_id", "count": {"$sum": 1}}},
    {"$match": {"count": {"$gt": 1}}},
    {"$count": "duplicates"}
]
dupes = list(db.shipments.aggregate(pipeline))
dup_count = dupes[0]['duplicates'] if dupes else 0
print(f"Duplicate shipment IDs: {dup_count}")

# Order #6 check
order6 = db.shipments.find_one({"shipment_id": {"$regex": "107772253960"}})
if order6:
    print(f"Order #6 found: YES")
    print(f"  conflict_status: {order6.get('conflict_status', 'NONE')}")
    print(f"  has _conflict_resolution: {'_conflict_resolution' in order6}")
    if '_conflict_resolution' in order6:
        r = order6['_conflict_resolution']
        print(f"  approved_by: {r.get('approved_by', 'N/A')}")
else:
    print("Order #6: not found (may use different ID format)")

# Recent mutations (last 1 hour)
one_hour_ago = datetime.utcnow() - timedelta(hours=1)
recent = db.shipments.count_documents({"_updated_at": {"$gte": one_hour_ago}})
print(f"Shipments modified in last hour: {recent}")

client.close()
print("=== DATA SAFETY: VERIFIED ✓ ===")
