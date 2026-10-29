from typing import Dict, List, Any
from sqlalchemy.orm import Session
from models import Ingredient, RecipeItem, MenuScheduleItem, FoodItem, ProcurementRecommendation

class ProcurementEngine:
    def __init__(self, db: Session):
        self.db = db

    def calculate_menu_ingredient_demand(self, menu_id: str) -> List[Dict[str, Any]]:
        # 1. Fetch all planned servings for this menu
        schedule = self.db.query(MenuScheduleItem).filter(MenuScheduleItem.menu_id == menu_id).all()
        if not schedule:
            # fallback to all current schedule items
            schedule = self.db.query(MenuScheduleItem).all()

        # Sum planned portions per food item
        food_portions: Dict[str, int] = {}
        for s in schedule:
            food_portions[s.food_item_id] = food_portions.get(s.food_item_id, 0) + s.planned_servings

        # 2. Map through recipes to aggregate required ingredient quantities
        ingredient_demand: Dict[str, float] = {}
        for food_id, portions in food_portions.items():
            recipes = self.db.query(RecipeItem).filter(RecipeItem.food_item_id == food_id).all()
            for r in recipes:
                ingredient_demand[r.ingredient_id] = (
                    ingredient_demand.get(r.ingredient_id, 0.0) + (r.quantity_per_portion * portions)
                )

        # 3. Compare with current stock in inventory
        results = []
        for ing_id, required_qty in ingredient_demand.items():
            ing = self.db.query(Ingredient).filter(Ingredient.id == ing_id).first()
            if not ing:
                continue

            current_stock = ing.current_stock
            reorder_threshold = ing.reorder_threshold
            net_shortfall = (required_qty + reorder_threshold * 0.5) - current_stock

            if net_shortfall > 0:
                # Supplier minimum batching (e.g. round up to multiple of 5 or 10)
                order_multiple = 5.0 if ing.unit == "kg" else 1.0
                suggested_order = float(int((net_shortfall + order_multiple - 0.01) / order_multiple) * order_multiple)
                urgency = "Urgent" if current_stock < reorder_threshold else "High"
                reason = (
                    f"Approved weekly menu requires {required_qty:.1f} {ing.unit}. "
                    f"Current stock is {current_stock:.1f} {ing.unit} (threshold: {reorder_threshold} {ing.unit}). "
                    f"Shortfall of {net_shortfall:.1f} {ing.unit} requires purchasing {suggested_order:.1f} {ing.unit}."
                )
            else:
                suggested_order = 0.0
                urgency = "Normal"
                reason = f"Current stock ({current_stock:.1f} {ing.unit}) is sufficient to cover required {required_qty:.1f} {ing.unit}."

            results.append({
                "ingredient_id": ing.id,
                "ingredient_name": ing.name,
                "category": ing.category,
                "current_stock": current_stock,
                "required_for_menu": round(required_qty, 1),
                "unit": ing.unit,
                "avg_cost": ing.avg_cost,
                "reorder_threshold": reorder_threshold,
                "suggested_order": suggested_order,
                "estimated_procurement_cost": round(suggested_order * ing.avg_cost, 2),
                "supplier": ing.supplier,
                "lead_time_days": ing.lead_time_days,
                "urgency": urgency,
                "reason": reason
            })

        # Sort by urgency
        urgency_order = {"Urgent": 0, "High": 1, "Normal": 2}
        results.sort(key=lambda x: urgency_order.get(x["urgency"], 3))
        return results

    def record_stock_adjustment(self, ingredient_id: str, delta: float, reason: str = "Usage") -> Ingredient:
        ing = self.db.query(Ingredient).filter(Ingredient.id == ingredient_id).first()
        if not ing:
            raise ValueError("Ingredient not found")

        ing.current_stock = max(0.0, round(ing.current_stock + delta, 2))
        if ing.current_stock == 0:
            ing.status = "Critical"
        elif ing.current_stock <= ing.reorder_threshold:
            ing.status = "Low Stock"
        else:
            ing.status = "Normal"

        self.db.commit()
        self.db.refresh(ing)
        return ing
