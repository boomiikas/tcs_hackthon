import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any
from sqlalchemy.orm import Session
from models import DailyOperation, FoodItem, Canteen

class ForecastingEngine:
    def __init__(self, db: Session):
        self.db = db

    def generate_item_forecast(
        self,
        canteen_id: str,
        food_item_id: str,
        target_date: str,
        buffer_strategy: str = "balanced", # aggressive, balanced, conservative
        kitchen_capacity: int = 400
    ) -> Dict[str, Any]:
        item = self.db.query(FoodItem).filter(FoodItem.id == food_item_id).first()
        if not item:
            raise ValueError(f"Item {food_item_id} not found")

        # 1. Fetch historical operations for this item and canteen
        records = (
            self.db.query(DailyOperation)
            .filter(
                DailyOperation.canteen_id == canteen_id,
                DailyOperation.food_item_id == food_item_id
            )
            .order_by(DailyOperation.date.asc())
            .all()
        )

        if not records:
            # Baseline default
            base = item.standard_batch_size * 2
            return {
                "food_item_id": item.id,
                "food_name": item.name,
                "category": item.category,
                "meal_period": item.meal_period,
                "base_price": item.base_price,
                "prep_cost": item.prep_cost,
                "predicted_demand": base,
                "confidence_lower": int(base * 0.85),
                "confidence_upper": int(base * 1.15),
                "recommended_prep": base,
                "suggested_buffer": 4,
                "critical_ratio": 0.60,
                "shortage_risk": 5.0,
                "leftover_risk": 5.0,
                "staged_strategy": {"batch_1": int(base * 0.7), "batch_2": int(base * 0.3), "reassessment_trigger": "12:30 PM"},
                "explanation": "Cold start: using standard catalog batch recommendations."
            }

        # 2. Extract time series features
        # Day of week factor
        target_dt = datetime.strptime(target_date, "%Y-%m-%d")
        target_dow = target_dt.weekday()

        recent_records = records[-28:] # last 4 weeks
        same_dow_sales = [
            r.portions_sold for r in recent_records
            if datetime.strptime(r.date, "%Y-%m-%d").weekday() == target_dow
        ]
        all_recent_sales = [r.portions_sold for r in recent_records]

        # Calculate baseline & dow seasonality
        overall_mean = np.mean(all_recent_sales) if all_recent_sales else item.standard_batch_size * 2
        dow_mean = np.mean(same_dow_sales) if same_dow_sales else overall_mean

        # Linear trend calculation over the last 14 days
        y = np.array([r.portions_sold for r in records[-14:]])
        x = np.arange(len(y))
        if len(y) > 2:
            slope, intercept = np.polyfit(x, y, 1)
            trend_adj = slope * 2.0 # projected 2 periods forward
        else:
            trend_adj = 0.0

        raw_prediction = float(0.65 * dow_mean + 0.35 * overall_mean + trend_adj)
        predicted_demand = max(10, int(round(raw_prediction)))

        # 3. Uncertainty estimation (residual variance)
        residuals = [abs(r.portions_sold - r.predicted_demand) for r in recent_records if r.predicted_demand > 0]
        std_dev = np.std(residuals) if len(residuals) > 3 else (predicted_demand * 0.12)
        std_dev = max(3.0, std_dev)

        conf_lower = max(5, int(round(predicted_demand - 1.645 * std_dev)))
        conf_upper = int(round(predicted_demand + 1.645 * std_dev))

        # 4. Newsvendor Critical Fractile for Buffer Planning
        # Cu = understocking cost (lost gross margin = price - prep_cost)
        # Co = overstocking cost (prep_cost - surplus salvage value ~ 0.5 * prep_cost)
        cu = item.base_price - item.prep_cost
        salvage_value = item.prep_cost * 0.50
        co = item.prep_cost - salvage_value
        critical_ratio = cu / (cu + co)

        # Buffer strategy multiplier
        strategy_weights = {
            "conservative": 0.5, # minimize waste, willing to risk small stockout
            "balanced": 1.0,     # standard critical fractile
            "aggressive": 1.4    # minimize stockout, capture all demand
        }
        mult = strategy_weights.get(buffer_strategy, 1.0)

        # Safety buffer = z * std_dev
        z_score = (critical_ratio - 0.5) * 2.0 * mult
        buffer = max(2, int(round(z_score * std_dev * 0.6)))
        if buffer_strategy == "conservative":
            buffer = max(1, int(buffer * 0.5))

        prep_proposal = predicted_demand + buffer

        # Respect kitchen capacity and batch size increments
        batch_size = item.standard_batch_size
        batch_aligned_prep = int(np.ceil(prep_proposal / batch_size) * batch_size)
        final_recommended = min(kitchen_capacity, batch_aligned_prep)

        # Calculate shortage and leftover risks
        shortage_risk = round(float(np.clip((1.0 - critical_ratio) * 12.0 * (1.0 / mult), 2.0, 25.0)), 1)
        leftover_risk = round(float(np.clip(critical_ratio * 10.0 * mult, 2.0, 20.0)), 1)

        # Staged preparation logic
        stage_1 = int(round(final_recommended * 0.70))
        stage_2 = final_recommended - stage_1
        trigger = "12:15 PM" if item.meal_period == "Lunch" else ("07:30 PM" if item.meal_period == "Dinner" else "08:30 AM")

        explanation = (
            f"Historical DOW mean is {dow_mean:.1f} with trend factor {trend_adj:+.1f}. "
            f"Underage margin is ₹{cu:.1f} vs overage risk ₹{co:.1f} (CR: {critical_ratio:.2f}). "
            f"Optimal buffer of {buffer} portions aligns to {final_recommended // batch_size} kitchen batches of {batch_size} units."
        )

        return {
            "food_item_id": item.id,
            "food_name": item.name,
            "category": item.category,
            "meal_period": item.meal_period,
            "base_price": item.base_price,
            "prep_cost": item.prep_cost,
            "predicted_demand": predicted_demand,
            "confidence_lower": conf_lower,
            "confidence_upper": conf_upper,
            "recommended_prep": final_recommended,
            "suggested_buffer": buffer,
            "critical_ratio": round(critical_ratio, 3),
            "shortage_risk": shortage_risk,
            "leftover_risk": leftover_risk,
            "staged_strategy": {
                "batch_1": stage_1,
                "batch_2": stage_2,
                "reassessment_trigger": trigger
            },
            "explanation": explanation
        }

    def forecast_entire_horizon(
        self,
        canteen_id: str,
        start_date: str,
        days: int = 7,
        meal_period: str = "All",
        category: str = "All",
        buffer_strategy: str = "balanced",
        kitchen_capacity: int = 1200
    ) -> List[Dict[str, Any]]:
        query = self.db.query(FoodItem)
        if meal_period != "All":
            query = query.filter(FoodItem.meal_period == meal_period)
        if category != "All":
            query = query.filter(FoodItem.category == category)
        items = query.all()

        results = []
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")

        for d in range(days):
            cur_date = (start_dt + timedelta(days=d)).strftime("%Y-%m-%d")
            for item in items:
                res = self.generate_item_forecast(
                    canteen_id=canteen_id,
                    food_item_id=item.id,
                    target_date=cur_date,
                    buffer_strategy=buffer_strategy,
                    kitchen_capacity=kitchen_capacity
                )
                res["forecast_date"] = cur_date
                results.append(res)
        return results
