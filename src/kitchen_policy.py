"""Kitchen preparation policies and operational accounting for college canteens."""

from typing import Dict, Any, List
import numpy as np
import pandas as pd


class KitchenSimulator:
    """Simulates realistic kitchen preparation decisions, sales, waste, and financial accounting."""

    def __init__(
        self,
        policy: str = "buffered_forecast",
        buffer_pct: float = 0.10,
        batch_size: int = 5,
        waste_disposal_cost: float = 2.0,
        random_seed: int = 42,
    ):
        self.policy = policy
        self.buffer_pct = buffer_pct
        self.batch_size = batch_size
        self.waste_disposal_cost = waste_disposal_cost
        self.rng = np.random.RandomState(random_seed)

    def determine_preparation_quantity(
        self,
        demand_estimate: int,
        item_history: List[int],
        batch_size: int = 5,
    ) -> int:
        """Determine quantity prepared according to the configured kitchen policy.

        Args:
            demand_estimate: The realized underlying demand for today.
            item_history: Recent demand history for this item (e.g. past same-day or past days).
            batch_size: Kitchen cooking batch size increment.

        Returns:
            qty_prepared: Non-negative integer portions prepared.
        """
        if self.policy == "oracle":
            # Perfect foresight benchmark
            return demand_estimate

        elif self.policy == "naive_last_week":
            # Chef prepares what was demanded on the same day last week
            if item_history:
                baseline = item_history[-1]
            else:
                baseline = demand_estimate
            # Chef rounds up to nearest batch size
            prep = int(np.ceil(max(1, baseline) / batch_size) * batch_size)
            return max(0, prep)

        elif self.policy == "static_capacity":
            # Fixed capacity based on historical average
            baseline = np.mean(item_history) if item_history else demand_estimate
            prep = int(np.ceil(max(1, baseline) / batch_size) * batch_size)
            return max(0, prep)

        elif self.policy == "buffered_forecast":
            # Realistic canteen chef heuristic:
            # Chef tracks moving average demand, adds a safety buffer to avoid stockouts,
            # suffers human estimation error (+/- 8%), and batches production.
            if len(item_history) >= 2:
                # 2-week weighted moving average
                weights = [0.4, 0.6] if len(item_history) == 2 else [0.2, 0.3, 0.5]
                baseline = np.average(item_history[-len(weights):], weights=weights)
            elif item_history:
                baseline = item_history[-1]
            else:
                baseline = demand_estimate

            # Apply chef safety buffer (+10%)
            buffered = baseline * (1.0 + self.buffer_pct)

            # Chef human error / cognitive bias (Gaussian noise with 8% std)
            human_error = self.rng.normal(0.0, 0.08)
            planned = buffered * (1.0 + human_error)

            # Round to kitchen batch size (e.g. trays of 5 or 10)
            if planned <= 0:
                prep = 0
            else:
                prep = int(np.ceil(planned / batch_size) * batch_size)

            return max(0, prep)

        else:
            raise ValueError(f"Unknown preparation policy: {self.policy}")

    def execute_daily_accounting(
        self,
        demand_estimate: int,
        qty_prepared: int,
        selling_price: float,
        unit_cost: float,
    ) -> Dict[str, Any]:
        """Compute operational and financial accounting identities.

        Identities strictly enforced:
          qty_sold = min(demand_estimate, qty_prepared)
          qty_wasted = max(0, qty_prepared - qty_sold)
          stockout_flag = int(demand_estimate > qty_prepared)
          missed_demand = max(0, demand_estimate - qty_prepared)
          revenue = qty_sold * selling_price
          preparation_cost = qty_prepared * unit_cost
          waste_cost = qty_wasted * unit_cost + qty_wasted * waste_disposal_cost
          profit = revenue - preparation_cost - (qty_wasted * waste_disposal_cost)
        """
        qty_prepared = max(0, int(qty_prepared))
        demand_estimate = max(0, int(demand_estimate))

        qty_sold = min(demand_estimate, qty_prepared)
        qty_wasted = max(0, qty_prepared - qty_sold)
        stockout_flag = int(demand_estimate > qty_prepared)
        missed_demand = max(0, demand_estimate - qty_prepared)

        revenue = round(qty_sold * selling_price, 2)
        preparation_cost = round(qty_prepared * unit_cost, 2)
        waste_cost = round(qty_wasted * (unit_cost + self.waste_disposal_cost), 2)

        # Net Profit: Revenue - Direct Prep Cost - Disposal fees on wasted items
        profit = round(revenue - preparation_cost - (qty_wasted * self.waste_disposal_cost), 2)

        return {
            "demand_estimate": demand_estimate,
            "qty_prepared": qty_prepared,
            "qty_sold": qty_sold,
            "qty_wasted": qty_wasted,
            "stockout_flag": stockout_flag,
            "missed_demand": missed_demand,
            "revenue": revenue,
            "preparation_cost": preparation_cost,
            "waste_cost": waste_cost,
            "profit": profit,
        }
