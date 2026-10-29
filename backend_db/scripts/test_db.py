from pathlib import Path
import sys

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.core.mongodb import client, db, check_connection

collections = [
    "food_items",
    "sales_history",
    "demand_forecasts",
    "rescue_offers",
    "menu_plans"
]

try:
    check_connection()
    print("MongoDB Atlas connected!")

    existing = set(db.list_collection_names())

    for name in collections:
        if name not in existing:
            db.create_collection(name)
            print(f"Created: {name}")
        else:
            print(f"Already exists: {name}")

    print("Database setup completed!")

finally:
    client.close()