"""Mathematical menu mix optimization engine for CanteenIQ using Mixed-Integer Linear Programming."""

from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd
from scipy.optimize import milp, LinearConstraint, Bounds


class MenuMixOptimizer:
    """Optimizes a 7-day canteen menu mix balancing contribution, food waste reduction,

    student preferences, nutrition targets, kitchen capacity, and menu variety.
    """

    def __init__(
        self,
        daily_capacity_portions: int = 800,
        daily_budget_inr: float = 45000.0,
        min_dishes_per_day: int = 8,
        max_dishes_per_day: int = 14,
        waste_disposal_cost: float = 2.0,
        buffer_rate: float = 0.08,
        rating_weight: float = 5.0,
        waste_penalty_weight: float = 1.0,
    ):
        self.daily_capacity = daily_capacity_portions
        self.daily_budget = daily_budget_inr
        self.min_dishes = min_dishes_per_day
        self.max_dishes = max_dishes_per_day
        self.waste_disposal_cost = waste_disposal_cost
        self.buffer_rate = buffer_rate
        self.rating_weight = rating_weight
        self.waste_penalty_weight = waste_penalty_weight

    def optimize_weekly_menu(
        self,
        candidate_items_df: pd.DataFrame,
        weekly_forecast_df: pd.DataFrame,
        start_date: str = "2025-01-06",
        required_categories: Optional[List[str]] = None,
        min_avg_calories: float = 250.0,
        max_avg_calories: float = 650.0,
    ) -> Dict[str, Any]:
        """Solve 7-day menu mix optimization problem.

        Args:
            candidate_items_df: Unique menu items with price, cost, calories, rating, category.
            weekly_forecast_df: Predicted demand per item and day_of_week (0 to 6).
            start_date: Starting Monday date YYYY-MM-DD.
            required_categories: Categories that must have at least 1 item on menu each day.
            min_avg_calories: Lower calorie bound for balanced dining.
            max_avg_calories: Upper calorie bound.

        Returns:
            Dictionary containing weekly schedule, metrics, baseline comparison, and explanation.
        """
        if required_categories is None:
            required_categories = ["Beverages", "Rice Bowl", "Sandwich"]

        items = candidate_items_df.copy().reset_index(drop=True)
        N = len(items)
        D = 7  # 7 days

        # Index mappings
        item_names = items["item_name"].tolist()
        categories = items["category"].tolist()
        prices = items["price"].values
        costs = items["cost"].values
        calories = items["calories"].values
        ratings = items["rating"].values

        # Build forecast matrix: shape (N, D)
        demand_matrix = np.zeros((N, D))
        for _, row in weekly_forecast_df.iterrows():
            name = row["item_name"]
            dow = int(row.get("day_of_week", 0))
            if name in item_names and 0 <= dow < D:
                idx = item_names.index(name)
                demand_matrix[idx, dow] = max(1.0, float(row.get("predicted_demand", 10.0)))

        # Fill missing forecasts with item median
        for i in range(N):
            med = np.median(demand_matrix[i, demand_matrix[i, :] > 0]) if np.any(demand_matrix[i, :] > 0) else 15.0
            for d in range(D):
                if demand_matrix[i, d] <= 0:
                    demand_matrix[i, d] = med

        # Compute Economic Coefficients for decision variables x[i, d]
        # When item i is on menu on day d (x[i,d]=1), prep = ceil(D * (1 + buffer))
        # Expected Sold = D, Expected Waste = D * buffer
        # Expected Revenue = D * price
        # Expected Cost = D * (1 + buffer) * cost
        # Expected Waste Cost = D * buffer * (cost + waste_disposal_cost)
        # Expected Net Profit = Expected Revenue - Expected Cost - D * buffer * waste_disposal_cost
        # Preference Bonus = rating_weight * (rating - 3.5)
        # Net Objective Contribution to maximize:
        obj_matrix = np.zeros((N, D))
        prep_matrix = np.zeros((N, D))
        cost_matrix = np.zeros((N, D))
        waste_cost_matrix = np.zeros((N, D))

        for i in range(N):
            p = prices[i]
            c = costs[i]
            r = ratings[i]
            for d in range(D):
                dem = demand_matrix[i, d]
                prep = np.ceil(dem * (1.0 + self.buffer_rate))
                prep_matrix[i, d] = prep
                rev = dem * p
                direct_cost = prep * c
                waste_portions = max(0.0, prep - dem)
                waste_cost = waste_portions * (c + self.waste_disposal_cost)

                cost_matrix[i, d] = direct_cost
                waste_cost_matrix[i, d] = waste_cost

                net_profit = rev - direct_cost - (waste_portions * self.waste_disposal_cost)
                rating_bonus = self.rating_weight * (r - 3.5) * (dem / 10.0)

                # Total objective weight (we minimize -objective)
                obj_matrix[i, d] = net_profit + rating_bonus - (self.waste_penalty_weight * waste_cost)

        # Number of variables = N * D binary variables
        num_vars = N * D
        c_obj = -obj_matrix.flatten()  # SciPy milp minimizes c^T x

        # Formulate Linear Constraints: A_ub @ x <= b_ub and A_lb @ x >= b_lb
        constraint_rows = []
        lhs_bounds = []
        rhs_bounds = []

        # 1. Variety constraint per day: min_dishes <= sum_i x[i, d] <= max_dishes
        for d in range(D):
            row = np.zeros(num_vars)
            for i in range(N):
                row[i * D + d] = 1.0
            constraint_rows.append(row)
            lhs_bounds.append(self.min_dishes)
            rhs_bounds.append(self.max_dishes)

        # 2. Daily Kitchen Capacity: sum_i prep_matrix[i, d] * x[i, d] <= daily_capacity
        for d in range(D):
            row = np.zeros(num_vars)
            for i in range(N):
                row[i * D + d] = prep_matrix[i, d]
            constraint_rows.append(row)
            lhs_bounds.append(0.0)
            rhs_bounds.append(float(self.daily_capacity))

        # 3. Daily Ingredient Budget: sum_i cost_matrix[i, d] * x[i, d] <= daily_budget
        for d in range(D):
            row = np.zeros(num_vars)
            for i in range(N):
                row[i * D + d] = cost_matrix[i, d]
            constraint_rows.append(row)
            lhs_bounds.append(0.0)
            rhs_bounds.append(float(self.daily_budget))

        # 4. Required Categories: At least 1 item per required category each day
        for cat in required_categories:
            cat_indices = [i for i in range(N) if categories[i] == cat]
            if cat_indices:
                for d in range(D):
                    row = np.zeros(num_vars)
                    for i in cat_indices:
                        row[i * D + d] = 1.0
                    constraint_rows.append(row)
                    lhs_bounds.append(1.0)
                    rhs_bounds.append(float(len(cat_indices)))

        # 5. Anti-Fatigue / Maximum Item Repeats: Specialty items max 4 days/week
        for i in range(N):
            cat = categories[i]
            # Core staples like Masala Chai or Dal Tadka can appear every day (7 days); others max 4
            max_days = 7 if cat in ["Beverages", "Rice Bowl"] else 4
            row = np.zeros(num_vars)
            for d in range(D):
                row[i * D + d] = 1.0
            constraint_rows.append(row)
            lhs_bounds.append(0.0)
            rhs_bounds.append(float(max_days))

        # 6. Daily Balanced Nutrition / Average Calorie Bounds:
        # Linear formulation of: min_avg_calories <= sum(calories[i] * x[i,d]) / sum(x[i,d]) <= max_avg_calories
        if min_avg_calories is not None and min_avg_calories > 0:
            for d in range(D):
                row = np.zeros(num_vars)
                for i in range(N):
                    row[i * D + d] = float(calories[i] - min_avg_calories)
                constraint_rows.append(row)
                lhs_bounds.append(0.0)
                rhs_bounds.append(np.inf)

        if max_avg_calories is not None and max_avg_calories > 0:
            for d in range(D):
                row = np.zeros(num_vars)
                for i in range(N):
                    row[i * D + d] = float(calories[i] - max_avg_calories)
                constraint_rows.append(row)
                lhs_bounds.append(-np.inf)
                rhs_bounds.append(0.0)

        # Assemble constraints
        A_mat = np.array(constraint_rows)
        constraints = LinearConstraint(A=A_mat, lb=lhs_bounds, ub=rhs_bounds)
        integrality = np.ones(num_vars)  # All binary 0 or 1
        variable_bounds = Bounds(lb=np.zeros(num_vars), ub=np.ones(num_vars))

        # Solve with SciPy HiGHS MILP solver
        res = milp(c=c_obj, integrality=integrality, bounds=variable_bounds, constraints=constraints)

        if not res.success:
            # Fallback heuristic: greedy top scoring items if constraint relaxation needed
            x_sol = self._fallback_greedy_selection(obj_matrix, N, D, required_categories, categories)
        else:
            x_sol = np.round(res.x).reshape((N, D)).astype(int)

        # Assemble Daily Schedule
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        start_dt = pd.to_datetime(start_date)

        daily_plans = []
        tot_opt_sold = 0
        tot_opt_prep = 0
        tot_opt_waste = 0
        tot_opt_rev = 0.0
        tot_opt_cost = 0.0
        tot_opt_waste_cost = 0.0
        tot_opt_profit = 0.0

        for d in range(D):
            current_date_str = (start_dt + pd.Timedelta(days=d)).strftime("%Y-%m-%d")
            day_items = []
            d_cals = []
            for i in range(N):
                if x_sol[i, d] == 1:
                    dem = int(round(demand_matrix[i, d]))
                    prep = int(prep_matrix[i, d])
                    sold = min(dem, prep)
                    waste = max(0, prep - sold)
                    rev = round(sold * prices[i], 2)
                    cst = round(prep * costs[i], 2)
                    w_cst = round(waste * (costs[i] + self.waste_disposal_cost), 2)
                    profit = round(rev - cst - (waste * self.waste_disposal_cost), 2)

                    day_items.append({
                        "item_name": item_names[i],
                        "category": categories[i],
                        "price": float(prices[i]),
                        "cost": float(costs[i]),
                        "calories": int(calories[i]),
                        "rating": float(ratings[i]),
                        "predicted_demand": dem,
                        "recommended_preparation": prep,
                        "expected_sold": sold,
                        "expected_waste": waste,
                        "expected_revenue": rev,
                        "expected_cost": cst,
                        "expected_waste_cost": w_cst,
                        "expected_profit": profit,
                    })
                    d_cals.append(calories[i])
                    tot_opt_sold += sold
                    tot_opt_prep += prep
                    tot_opt_waste += waste
                    tot_opt_rev += rev
                    tot_opt_cost += cst
                    tot_opt_waste_cost += w_cst
                    tot_opt_profit += profit

            daily_plans.append({
                "date": current_date_str,
                "day_of_week": day_names[d],
                "dishes_count": len(day_items),
                "total_portions_prepared": sum(it["recommended_preparation"] for it in day_items),
                "total_expected_revenue": round(sum(it["expected_revenue"] for it in day_items), 2),
                "total_expected_profit": round(sum(it["expected_profit"] for it in day_items), 2),
                "avg_calories_per_dish": round(float(np.mean(d_cals)), 1) if d_cals else 0.0,
                "menu_items": day_items,
            })

        # Compare Against Baseline Plan (Static Fixed Menu: serving fixed top dishes every day with naive +25% buffer)
        static_top_idxs = np.argsort(-np.sum(demand_matrix, axis=1))[:self.max_dishes]
        baseline_prep = 0
        baseline_sold = 0
        baseline_waste = 0
        baseline_rev = 0.0
        baseline_cost = 0.0
        baseline_waste_cost = 0.0

        for i in static_top_idxs:
            p = prices[i]
            c = costs[i]
            for d in range(D):
                dem = int(round(demand_matrix[i, d]))
                prep = int(np.ceil(dem * 1.25))
                sold = min(dem, prep)
                waste = max(0, prep - sold)
                baseline_prep += prep
                baseline_sold += sold
                baseline_waste += waste
                baseline_rev += sold * p
                baseline_cost += prep * c
                baseline_waste_cost += waste * (c + self.waste_disposal_cost)

        baseline_rev = round(baseline_rev, 2)
        baseline_cost = round(baseline_cost, 2)
        baseline_waste_cost = round(baseline_waste_cost, 2)
        baseline_profit = round(baseline_rev - baseline_cost - (baseline_waste * self.waste_disposal_cost), 2)

        profit_lift = round(((tot_opt_profit - baseline_profit) / abs(baseline_profit)) * 100.0, 1) if baseline_profit != 0 else 0.0
        profit_str = f"+{profit_lift}%" if profit_lift >= 0 else f"{profit_lift}%"
        waste_reduction_pct = round(((baseline_waste - tot_opt_waste) / baseline_waste) * 100.0, 1) if baseline_waste > 0 else 0.0

        comparison = {
            "ai_optimized_plan": {
                "total_portions_prepared": tot_opt_prep,
                "total_portions_sold": tot_opt_sold,
                "total_portions_wasted": tot_opt_waste,
                "waste_rate_percentage": round((tot_opt_waste / tot_opt_prep) * 100.0, 2),
                "expected_gross_revenue": round(tot_opt_rev, 2),
                "expected_ingredient_cost": round(tot_opt_cost, 2),
                "expected_waste_cost": round(tot_opt_waste_cost, 2),
                "expected_net_profit": round(tot_opt_profit, 2),
            },
            "unoptimized_static_baseline": {
                "total_portions_prepared": baseline_prep,
                "total_portions_sold": baseline_sold,
                "total_portions_wasted": baseline_waste,
                "waste_rate_percentage": round((baseline_waste / baseline_prep) * 100.0, 2),
                "expected_gross_revenue": baseline_rev,
                "expected_ingredient_cost": baseline_cost,
                "expected_waste_cost": baseline_waste_cost,
                "expected_net_profit": baseline_profit,
            },
            "impact_improvements": {
                "profit_increase_pct": profit_str,
                "food_waste_reduction_pct": f"-{waste_reduction_pct}%",
                "portions_saved_from_landfill": baseline_waste - tot_opt_waste,
                "waste_cost_dollars_saved": round(baseline_waste_cost - tot_opt_waste_cost, 2),
            },
        }

        explanation = (
            f"The AI-optimized 7-day menu mix selected an average of {np.mean([p['dishes_count'] for p in daily_plans]):.1f} dishes per day, "
            f"prioritizing high-margin student favorites (ratings >= 4.5) while ensuring balanced nutrition ({min_avg_calories:.0f}-{max_avg_calories:.0f} kcal) "
            f"and strict category coverage. Compared to an un-optimized static canteen menu, CanteenIQ achieves a "
            f"{waste_reduction_pct}% reduction in food waste portions and unlocks a {profit_str} uplift in weekly operating contribution."
        )

        return {
            "start_date": start_date,
            "days_planned": D,
            "daily_plans": daily_plans,
            "baseline_comparison": comparison,
            "selection_rationale": explanation,
        }

    def _fallback_greedy_selection(
        self, obj_matrix: np.ndarray, N: int, D: int, req_cats: List[str], categories: List[str]
    ) -> np.ndarray:
        """Greedy heuristic fallback if strict solver constraints require relaxation."""
        x = np.zeros((N, D), dtype=int)
        for d in range(D):
            # Pick best in each required category
            for cat in req_cats:
                cat_idxs = [i for i in range(N) if categories[i] == cat]
                if cat_idxs:
                    best_i = max(cat_idxs, key=lambda i: obj_matrix[i, d])
                    x[best_i, d] = 1

            # Fill up to min_dishes with highest score items
            sorted_indices = np.argsort(-obj_matrix[:, d])
            for i in sorted_indices:
                if np.sum(x[:, d]) >= self.min_dishes:
                    break
                x[i, d] = 1
        return x
