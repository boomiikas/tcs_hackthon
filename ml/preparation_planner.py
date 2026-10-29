"""Buffer-based preparation planning and batch scheduling for CanteenIQ."""

from typing import Dict, Any, Optional, List
import math
import numpy as np


class PreparationPlanner:
    """Calculates kitchen preparation quantities using rule-based and adaptive buffers,

    respecting capacity bounds, cooking batch increments, and staged two-batch recommendations.
    """

    def __init__(
        self,
        default_buffer_pct: float = 0.10,
        default_kitchen_capacity: Optional[int] = 500,
        default_batch_size: int = 5,
    ):
        self.default_buffer_pct = default_buffer_pct
        self.default_kitchen_capacity = default_kitchen_capacity
        self.default_batch_size = default_batch_size

    def calculate_preparation(
        self,
        item_name: str,
        predicted_demand: float,
        buffer_pct: Optional[float] = None,
        kitchen_capacity: Optional[int] = None,
        min_batch_size: int = 0,
        batch_multiple: Optional[int] = None,
        enable_adaptive_buffer: bool = False,
        historical_waste_rate_pct: Optional[float] = None,
        demand_uncertainty_std: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Calculate recommended preparation portions for a single item.

        Formula:
          recommended_prep = min(kitchen_capacity, ceiling(predicted_demand * (1 + buffer_rate)))
        """
        predicted = max(0.0, float(predicted_demand))
        capacity = kitchen_capacity if kitchen_capacity is not None else self.default_kitchen_capacity
        batch_mult = batch_multiple if batch_multiple is not None else self.default_batch_size

        # 1. Determine Buffer Rate (Rule-based or Adaptive)
        if buffer_pct is not None:
            buffer_rate = float(buffer_pct)
        elif enable_adaptive_buffer:
            buffer_rate = self._compute_adaptive_buffer(
                predicted_demand=predicted,
                historical_waste_rate_pct=historical_waste_rate_pct,
                demand_uncertainty_std=demand_uncertainty_std,
            )
        else:
            buffer_rate = self.default_buffer_pct

        # 2. Check for Structural Constraint Conflicts
        capacity_conflict = False
        conflict_message = None
        if capacity is not None and min_batch_size > capacity:
            capacity_conflict = True
            conflict_message = (
                f"Configuration Conflict: Minimum batch quantity ({min_batch_size}) "
                f"exceeds maximum kitchen capacity ({capacity}) for {item_name}!"
            )

        # 3. Base Buffered Preparation
        if predicted == 0.0:
            recommended_prep = 0
            extra_portions = 0
        else:
            raw_buffered = round(predicted * (1.0 + buffer_rate), 6)
            base_prep = math.ceil(raw_buffered)

            # Round to batch cooking multiple (e.g. trays of 5)
            if batch_mult > 1:
                batched_prep = math.ceil(base_prep / batch_mult) * batch_mult
            else:
                batched_prep = base_prep

            # Apply minimum batch quantity
            if min_batch_size > 0:
                batched_prep = max(min_batch_size, batched_prep)

            # Apply kitchen capacity ceiling
            if capacity is not None:
                recommended_prep = min(capacity, batched_prep)
            else:
                recommended_prep = batched_prep

            extra_portions = max(0, recommended_prep - int(round(predicted)))

        # 4. Estimated Surplus & Risk
        estimated_surplus = max(0, recommended_prep - int(round(predicted)))

        # 5. Staged Cooking (Two-Batch Workflow)
        # Recommend cooking 70% in morning batch, keeping 30% for noon demand confirmation
        if recommended_prep >= 10:
            batch_1_portions = int(math.ceil((recommended_prep * 0.70) / max(1, batch_mult)) * max(1, batch_mult))
            batch_1_portions = min(recommended_prep, batch_1_portions)
            batch_2_portions = recommended_prep - batch_1_portions
            staged_plan = {
                "staged_cooking_enabled": True,
                "batch_1_morning": batch_1_portions,
                "batch_2_midday": batch_2_portions,
                "batch_2_trigger_rule": f"Cook Batch 2 ({batch_2_portions} portions) only if 12:30 PM demand exceeds {int(predicted * 0.60)} orders.",
            }
        else:
            staged_plan = {
                "staged_cooking_enabled": False,
                "batch_1_morning": recommended_prep,
                "batch_2_midday": 0,
                "batch_2_trigger_rule": "Single batch preparation recommended due to low portion volume.",
            }

        return {
            "item_name": item_name,
            "predicted_demand": round(predicted, 1),
            "buffer_percentage": round(buffer_rate * 100.0, 1),
            "buffer_portions": extra_portions,
            "recommended_preparation": recommended_prep,
            "estimated_surplus": estimated_surplus,
            "kitchen_capacity": capacity,
            "min_batch_size": min_batch_size,
            "batch_multiple": batch_mult,
            "has_capacity_conflict": capacity_conflict,
            "conflict_message": conflict_message,
            "staged_preparation": staged_plan,
        }

    def _compute_adaptive_buffer(
        self,
        predicted_demand: float,
        historical_waste_rate_pct: Optional[float],
        demand_uncertainty_std: Optional[float],
    ) -> float:
        """Dynamically adjust buffer based on waste history and demand volatility."""
        base = self.default_buffer_pct

        # If item has high historical waste (> 25%), reduce buffer to cut waste
        if historical_waste_rate_pct is not None and historical_waste_rate_pct > 25.0:
            waste_penalty = min(0.06, (historical_waste_rate_pct - 25.0) * 0.003)
            base -= waste_penalty

        # If item has high demand volatility (std / predicted > 0.3), add safety buffer
        if demand_uncertainty_std is not None and predicted_demand > 0:
            cv = demand_uncertainty_std / predicted_demand
            if cv > 0.30:
                base += min(0.08, (cv - 0.30) * 0.15)

        # Clamp between 2% and 25%
        return max(0.02, min(0.25, base))
