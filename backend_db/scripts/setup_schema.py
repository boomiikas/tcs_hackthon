
from pathlib import Path
import sys

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.core.mongodb import db

# Required fields for each MenuMind collection.
SCHEMAS = {
    "food_items": {
        "item_id": "string",
        "item_name": "string",
        "category": "string",
        "selling_price": "number",
        "preparation_cost": "number",
        "standard_batch_qty": "number",
        "minimum_batch_qty": "number",
        "calories_per_serving": "number",
        "protein_g": "number",
        "carbs_g": "number",
        "fat_g": "number",
        "fiber_g": "number",
        "allergens": "array",
        "active": "bool",
    },
    "sales_history": {
        "date": "string",
        "item_id": "string",
        "qty_prepared": "number",
        "qty_sold": "number",
        "qty_discounted": "number",
        "qty_wasted": "number",
        "remaining_qty": "number",
        "regular_price": "number",
        "discount_revenue": "number",
        "student_rating": "number",
    },
    "ingredients": {
        "ingredient_id": "string",
        "ingredient_name": "string",
        "stock_qty": "number",
        "unit": "string",
        "unit_cost": "number",
        "reorder_level": "number",
        "expiry_date": "string",
        "supplier_lead_days": "number",
    },
    "recipes": {
        "item_id": "string",
        "ingredient_id": "string",
        "quantity_required": "number",
        "unit": "string",
        "portions_per_batch": "number",
    },
    "student_feedback": {
        "date": "string",
        "item_id": "string",
        "rating": "number",
        "votes": "number",
        "preorders": "number",
    },
    "rescue_offers": {
        "listing_id": "string",
        "date": "string",
        "item_id": "string",
        "qty_available": "number",
        "original_price": "number",
        "discount_price": "number",
        "qty_reserved": "number",
        "qty_collected": "number",
        "collection_deadline": "string",
        "listing_status": "string",
        "final_disposition": "string",
    },
    "demand_forecasts": {
        "date": "string",
        "item_id": "string",
        "predicted_demand": "number",
        "actual_demand": "number",
        "model_version": "string",
    },
    "menu_plans": {
        "date": "string",
        "item_id": "string",
        "planned_qty": "number",
        "predicted_demand": "number",
        "budget": "number",
        "nutrition_summary": "object",
    },
    "calendar_events": {
        "date": "string",
        "day_of_week": "string",
        "is_holiday": "bool",
        "event_name": "string",
        "expected_attendance": "number",
    },
}

# Create validators for collections that don't exist yet.
# Existing collections receive the validator without deleting data.
for name, fields in SCHEMAS.items():
    validator = {
        "$jsonSchema": {
            "bsonType": "object",
            "required": list(fields.keys()),
            "properties": {
                field: {
                    "bsonType": (
                        ["int", "long", "double", "decimal"]
                        if kind == "number"
                        else [kind]
                    )
                }
                for field, kind in fields.items()
            },
        }
    }

    if name not in db.list_collection_names():
        db.create_collection(name, validator=validator)
        print(f"Created collection with schema: {name}")
    else:
        db.command({
            "collMod": name,
            "validator": validator,
            "validationLevel": "strict",
            "validationAction": "error",
        })
        print(f"Added/updated schema validator: {name}")

print("\nMenuMind schema setup completed.")
print("No existing documents were intentionally deleted.")
