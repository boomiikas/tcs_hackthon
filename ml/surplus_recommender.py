"""Rule-based surplus food discount recommendations, Mystery Meal bundling, and food safety gating."""

from typing import Dict, Any, List, Optional
import math


class SurplusFoodRecommender:
    """Manages surplus inventory discounting, rescue bundling, and food safety compliance."""

    DISCOUNT_TIERS = {
        "early_afternoon": {"window": "14:00 - 16:00", "discount_pct": 20.0, "label": "Early Afternoon Flash Deal"},
        "late_afternoon": {"window": "16:00 - 18:30", "discount_pct": 35.0, "label": "Sunset Canteen Rescue Deal"},
        "end_of_service": {"window": "18:30 - 20:30", "discount_pct": 50.0, "label": "Zero-Waste Last Chance Clearance"},
    }

    def __init__(self, waste_disposal_cost: float = 2.0):
        self.waste_disposal_cost = waste_disposal_cost

    def recommend_discounts(
        self,
        surplus_inventory: List[Dict[str, Any]],
        current_time_str: str = "16:30",
        manager_safety_override: bool = False,
    ) -> Dict[str, Any]:
        """Recommend tiered pricing discounts for unsold surplus food.

        Args:
            surplus_inventory: List of dicts with keys:
              'item_name', 'category', 'price', 'cost', 'surplus_portions',
              'holding_time_hours' (optional), 'holding_temp_celsius' (optional).
            current_time_str: Current military time HH:MM (e.g. '16:30').
            manager_safety_override: Manual safety approval flag if logs absent.

        Returns:
            Dictionary with discounted item recommendations, revenue recovery, and food safety status.
        """
        # Determine time-of-day discount tier
        tier_key = self._resolve_discount_tier(current_time_str)
        tier_info = self.DISCOUNT_TIERS[tier_key]
        discount_pct = tier_info["discount_pct"]
        discount_multiplier = 1.0 - (discount_pct / 100.0)

        discounted_items = []
        total_recovery_rev = 0.0
        total_waste_fees_saved = 0.0
        unsafe_items = []

        for item in surplus_inventory:
            name = item["item_name"]
            cat = item.get("category", "Main")
            price = float(item["price"])
            cost = float(item.get("cost", price * 0.5))
            surplus = int(item.get("surplus_portions", 0))

            if surplus <= 0:
                continue

            # Food Safety Screening
            safety_status = self._evaluate_food_safety(
                item_name=name,
                category=cat,
                holding_time_hours=item.get("holding_time_hours"),
                holding_temp_celsius=item.get("holding_temp_celsius"),
                manager_override=manager_safety_override,
            )

            if not safety_status["is_eligible_for_sale"]:
                unsafe_items.append({
                    "item_name": name,
                    "surplus_portions": surplus,
                    "reason": safety_status["safety_reason"],
                    "action_required": "COMPOST OR BIO-DIGEST IMMEDIATELY. DO NOT SERVE.",
                })
                continue

            discounted_price = round(price * discount_multiplier, 0)
            item_recovery = round(discounted_price * surplus, 2)
            item_waste_saved = round(surplus * self.waste_disposal_cost, 2)

            total_recovery_rev += item_recovery
            total_waste_fees_saved += item_waste_saved

            discounted_items.append({
                "item_name": name,
                "category": cat,
                "original_price_inr": price,
                "discount_percentage": discount_pct,
                "discounted_price_inr": discounted_price,
                "surplus_portions": surplus,
                "potential_recovery_revenue_inr": item_recovery,
                "food_safety": safety_status,
            })

        # Generate Mystery Meal Rescue Combos from eligible surplus
        mystery_combo = self._create_mystery_meal(discounted_items, tier_discount=discount_pct)

        return {
            "current_time": current_time_str,
            "applied_discount_tier": tier_info["label"],
            "discount_percentage": discount_pct,
            "eligible_surplus_items_count": len(discounted_items),
            "unsafe_disqualified_items_count": len(unsafe_items),
            "total_potential_recovery_revenue_inr": round(total_recovery_rev, 2),
            "total_disposal_costs_avoided_inr": round(total_waste_fees_saved, 2),
            "total_financial_value_salvaged_inr": round(total_recovery_rev + total_waste_fees_saved, 2),
            "discounted_items": discounted_items,
            "unsafe_items_flagged": unsafe_items,
            "mystery_meal_bundle": mystery_combo,
        }

    def _resolve_discount_tier(self, time_str: str) -> str:
        """Resolve applicable discount tier based on clock time."""
        try:
            parts = time_str.split(":")
            hour = int(parts[0])
            minute = int(parts[1]) if len(parts) > 1 else 0
            time_val = hour + (minute / 60.0)

            if time_val < 16.0:
                return "early_afternoon"
            elif time_val < 18.5:
                return "late_afternoon"
            else:
                return "end_of_service"
        except Exception:
            return "late_afternoon"

    def _evaluate_food_safety(
        self,
        item_name: str,
        category: str,
        holding_time_hours: Optional[float],
        holding_temp_celsius: Optional[float],
        manager_override: bool,
    ) -> Dict[str, Any]:
        """Verify strict HACCP / FSSAI food safety guidelines for prepared food."""
        # Ambient packaged beverages & dry snacks are shelf-stable
        if category in ["Beverages", "Extras"] and "Chai" not in item_name and "Coffee" not in item_name:
            return {
                "is_eligible_for_sale": True,
                "requires_manual_inspection": False,
                "safety_reason": "Shelf-stable or packaged ambient food item.",
            }

        # Hot-holding prepared dishes (Rice Bowls, Pastas, Pizzas, Curries)
        # Limit: max 4 hours holding time above 60°C
        if holding_time_hours is not None:
            if holding_time_hours > 4.0:
                return {
                    "is_eligible_for_sale": False,
                    "requires_manual_inspection": False,
                    "safety_reason": f"Holding time exceeded ({holding_time_hours:.1f}h > 4.0h limit). Risk of bacterial proliferation.",
                }
            if holding_temp_celsius is not None and holding_temp_celsius < 55.0:
                return {
                    "is_eligible_for_sale": False,
                    "requires_manual_inspection": False,
                    "safety_reason": f"Temperature danger zone detected ({holding_temp_celsius}°C < 60°C).",
                }
            # Within safe holding duration (<= 4.0h)
            return {
                "is_eligible_for_sale": True,
                "requires_manual_inspection": holding_temp_celsius is None,
                "safety_reason": "Within safe holding time (< 4.0h). Manual temperature/aroma check advised before packing.",
            }

        # If automated logs absent, require manager manual sensory/temperature sign-off
        return {
            "is_eligible_for_sale": True if manager_override else False,
            "requires_manual_inspection": True,
            "safety_reason": "Manual confirmation required: holding time not logged. Verify hot holding temperature (>= 60°C) and sensory aroma before packing.",
        }

    def _create_mystery_meal(
        self, eligible_items: List[Dict[str, Any]], tier_discount: float
    ) -> Dict[str, Any]:
        """Bundle surplus items into an appetizing Mystery Meal Eco-Rescue Box."""
        if not eligible_items:
            return {"available": False, "message": "No eligible surplus items available for mystery bundling."}

        mains = [it for it in eligible_items if it["category"] in ["Rice Bowl", "Sandwich", "Pasta", "Pizza", "Biryani"]]
        beverages = [it for it in eligible_items if it["category"] == "Beverages"]
        snacks = [it for it in eligible_items if it["category"] in ["Starters", "Other Snacks", "Extras", "Desert", "Salad"]]

        selected = []
        if mains:
            selected.append(max(mains, key=lambda x: x["surplus_portions"]))
        if beverages:
            selected.append(max(beverages, key=lambda x: x["surplus_portions"]))
        if snacks:
            selected.append(max(snacks, key=lambda x: x["surplus_portions"]))

        if len(selected) < 2:
            selected = sorted(eligible_items, key=lambda x: -x["surplus_portions"])[:2]

        orig_sum = sum(it["original_price_inr"] for it in selected)
        # Apply 10% extra combo bonus on top of tier discount
        combo_discount = min(60.0, tier_discount + 10.0)
        combo_price = round(orig_sum * (1.0 - combo_discount / 100.0), 0)
        max_combos = min(it["surplus_portions"] for it in selected)

        return {
            "available": True,
            "bundle_title": "CanteenIQ Eco-Rescue Mystery Box",
            "bundled_items": [it["item_name"] for it in selected],
            "max_combos_packable": max_combos,
            "original_combined_price_inr": orig_sum,
            "mystery_discount_pct": combo_discount,
            "rescue_combo_price_inr": combo_price,
            "total_portions_rescued": len(selected) * max_combos,
            "collection_deadline": "Must be collected within 60 minutes of packing.",
        }
