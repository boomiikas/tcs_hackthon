
import csv
from pathlib import Path
import sys

from pymongo import ReplaceOne

# Allow this script to import the existing MongoDB connection.
BACKEND = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))

from app.core.mongodb import db

DATA_DIR = BACKEND / "data"

# Convert CSV text into appropriate Python values.
INTEGER_FIELDS = {
    "original_meal_id", "calories", "week_number", "is_holiday",
    "promotion", "demand_estimate", "qty_prepared", "qty_sold",
    "qty_wasted", "stockout_flag", "missed_demand", "days_offered",
    "stockout_days", "promotion_days", "votes", "preorders",
}

FLOAT_FIELDS = {
    "selling_price", "cost", "margin", "margin_pct", "base_rating",
    "price_elasticity", "rating", "revenue", "preparation_cost",
    "waste_cost", "profit", "avg_selling_price", "avg_cost",
    "avg_rating", "waste_rate_pct",
    "historical_mean_weekly_orders",
    "historical_mean_checkout_price",
    "historical_mean_base_price",
    "synthetic_selling_price", "synthetic_cost",
}

BOOL_FIELDS = {"is_synthetic"}


def convert_value(field, value):
    value = value.strip()

    if value == "":
        return None

    if field in INTEGER_FIELDS:
        return int(value)

    if field in FLOAT_FIELDS:
        return float(value)

    if field in BOOL_FIELDS:
        return value.lower() in {"true", "1", "yes"}

    # Keep dates as ISO strings, e.g. 2025-01-06.
    return value



def import_csv(filename, collection_name, key_fields):
    import time
    from pymongo.errors import NetworkTimeout, AutoReconnect

    path = DATA_DIR / filename

    if not path.is_file():
        raise FileNotFoundError(f"CSV file not found: {path}")

    collection = db[collection_name]
    batch_size = 50
    imported_count = 0
    operations = []

    def flush_batch():
        nonlocal imported_count, operations

        if not operations:
            return

        # Retry temporary network failures up to 3 times.
        for attempt in range(3):
            try:
                collection.bulk_write(operations, ordered=False)
                imported_count += len(operations)
                operations = []
                print(
                    f"{filename}: {imported_count} rows processed...",
                    flush=True,
                )
                return
            except (NetworkTimeout, AutoReconnect):
                if attempt == 2:
                    raise
                print(
                    f"Temporary connection issue. "
                    f"Retrying batch ({attempt + 1}/3)...",
                    flush=True,
                )
                time.sleep(3 * (attempt + 1))

    with path.open("r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)

        if not reader.fieldnames:
            raise ValueError(f"No header row found in {filename}")

        for row in reader:
            document = {
                field: convert_value(field, value or "")
                for field, value in row.items()
                if field is not None
            }

            if any(
                key not in document or document[key] is None
                or document[key] == ""
                for key in key_fields
            ):
                raise ValueError(
                    f"Missing key {key_fields} in {filename}, "
                    f"CSV row {reader.line_num}"
                )

            filter_query = {
                key: document[key] for key in key_fields
            }

            operations.append(
                ReplaceOne(filter_query, document, upsert=True)
            )

            if len(operations) >= batch_size:
                flush_batch()

        flush_batch()

    print(
        f"{filename} -> {collection_name}: "
        f"{imported_count} rows processed; "
        f"{collection.count_documents({})} documents now in collection"
    )


def main():
    # Unique indexes protect against duplicate logical records.
    db.food_items.create_index("item_id", unique=True)
    db.sales_history.create_index(
        [("date", 1), ("item_id", 1)], unique=True
    )
    db.weekly_sales.create_index(
        [("week_number", 1), ("item_id", 1)], unique=True
    )
    db.source_mapping.create_index("synthetic_item_id", unique=True)

    import_csv(
        "synthetic_menu_catalog.csv",
        "food_items",
        ["item_id"],
    )
    import_csv(
        "synthetic_canteen_daily.csv",
        "sales_history",
        ["date", "item_id"],
    )
    import_csv(
        "synthetic_canteen_weekly.csv",
        "weekly_sales",
        ["week_number", "item_id"],
    )
    import_csv(
        "source_mapping.csv",
        "source_mapping",
        ["synthetic_item_id"],
    )

    print("\nMenuMind CSV import completed.")


if __name__ == "__main__":
    main()
