
from pathlib import Path
import sys

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.core.mongodb import db

collections = [
    "food_items",
    "sales_history",
    "weekly_sales",
    "source_mapping",
]

existing = set(db.list_collection_names())

for name in collections:
    if name in existing:
        db.command({
            "collMod": name,
            "validator": {},
        })
        print(f"Removed conflicting validator: {name}")
    else:
        print(f"Collection not created yet: {name}")

print("Validator fix completed. Existing data was not deleted.")
