"""MenuMind Rewind: Retrospective Counterfactual Food Waste Simulator.

Enables retrospective 'what-if' simulation of alternative kitchen preparation
decisions against ground-truth simulated daily demand, calculating sales, waste,
profit, and multi-dimensional regret metrics.
"""

from typing import Dict, Any, List, Union
import pandas as pd
import numpy as np


class MenuMindRewindSimulator:
    """Retrospective counterfactual simulator for canteen food waste and profitability."""

    def __init__(self, waste_disposal_cost: float = 2.0):
        self.waste_disposal_cost = waste_disposal_cost

    def evaluate_decision(
        self,
        demand: int,
        prepared: int,
        selling_price: float,
        unit_cost: float,
        waste_disposal_cost: float = None,
    ) -> Dict[str, Any]:
        """Evaluate a single preparation quantity decision against known demand.

        Args:
            demand: Ground-truth realized demand (portions).
            prepared: Alternative candidate preparation quantity (portions).
            selling_price: Selling price per portion.
            unit_cost: Food/ingredient preparation cost per portion.
            waste_disposal_cost: Unit disposal fee for unsold food.

        Returns:
            Dictionary containing sales, waste, missed demand, financial metrics,
            and regrets relative to ex-post perfect foresight.
        """
        if waste_disposal_cost is None:
            waste_disposal_cost = self.waste_disposal_cost

        demand = max(0, int(demand))
        prepared = max(0, int(prepared))

        sold = min(demand, prepared)
        waste = max(0, prepared - demand)
        missed_demand = max(0, demand - prepared)

        revenue = round(sold * selling_price, 2)
        prep_cost = round(prepared * unit_cost, 2)
        disp_cost = round(waste * waste_disposal_cost, 2)
        net_profit = round(revenue - prep_cost - disp_cost, 2)

        # Ex-post optimal benchmark: exactly preparing demand (Q* = demand)
        optimal_profit = round(demand * (selling_price - unit_cost), 2)
        profit_regret = round(max(0.0, optimal_profit - net_profit), 2)

        # Waste Regret: avoidable expenditure on wasted portions
        waste_regret = round(waste * (unit_cost + waste_disposal_cost), 2)

        # Missed Demand Regret: unrealized gross margin on unserved diners
        margin_per_unit = max(0.0, selling_price - unit_cost)
        missed_demand_regret = round(missed_demand * margin_per_unit, 2)

        return {
            "portions_prepared": prepared,
            "portions_sold": sold,
            "leftover_portions": waste,
            "missed_demand": missed_demand,
            "revenue": revenue,
            "ingredient_cost": prep_cost,
            "waste_disposal_cost": disp_cost,
            "estimated_profit": net_profit,
            "optimal_profit": optimal_profit,
            "profit_regret": profit_regret,
            "waste_regret": waste_regret,
            "missed_demand_regret": missed_demand_regret,
            "stockout_flag": int(demand > prepared),
        }

    def simulate_quantity_sweep(
        self,
        date: str,
        item_id: str,
        item_name: str,
        demand: int,
        actual_prepared: int,
        selling_price: float,
        unit_cost: float,
        step: int = 5,
        range_padding: int = 25,
    ) -> pd.DataFrame:
        """Run a sweep of counterfactual preparation quantities for a specific item on a date.

        Args:
            date: Operating date string.
            item_id: Synthetic item ID.
            item_name: Dish name.
            demand: Ground-truth realized demand.
            actual_prepared: Historical simulated prep decision.
            selling_price: Price per portion.
            unit_cost: Unit cost.
            step: Quantity increment for sweep.
            range_padding: Units below/above to sweep across.

        Returns:
            DataFrame with sweep comparisons across all tested quantities.
        """
        min_q = max(0, min(demand, actual_prepared) - range_padding)
        max_q = max(demand, actual_prepared) + range_padding

        # Round min_q down and max_q up to step
        min_q = (min_q // step) * step
        max_q = int(np.ceil(max_q / step)) * step

        candidate_quantities = sorted(list(set(
            list(range(min_q, max_q + 1, step)) + [actual_prepared, demand]
        )))

        rows = []
        for q in candidate_quantities:
            res = self.evaluate_decision(demand, q, selling_price, unit_cost)
            res["date"] = date
            res["item_id"] = item_id
            res["item_name"] = item_name
            res["ground_truth_demand"] = demand
            res["is_actual_decision"] = (q == actual_prepared)
            res["is_oracle_optimal"] = (q == demand)
            rows.append(res)

        return pd.DataFrame(rows)

    def compare_retrospective_policies(
        self,
        daily_df: pd.DataFrame,
    ) -> pd.DataFrame:
        """Compare multiple kitchen preparation policies across the entire daily dataset.

        Policies tested:
          1. Actual Simulated Chef: the decisions recorded in daily_df.
          2. MenuMind AI Smart Buffer (+5%): Lean buffer matching demand smoothly.
          3. Aggressive Kitchen (+25%): High food buffer policy.
          4. Conservative Kitchen (-15%): Lean cost-cutting policy.
          5. Ex-Post Oracle (0% waste): Upper bound benchmark.

        Returns:
            DataFrame summarizing total sold, wasted, missed demand, profit, and waste regret.
        """
        policies = {
            "Actual Simulated Chef": lambda row: row["qty_prepared"],
            "MenuMind AI Recommendation": lambda row: int(np.ceil(row["demand_estimate"] * 1.05 / 5) * 5),
            "Aggressive Over-Preparation (+25%)": lambda row: int(np.ceil(row["demand_estimate"] * 1.25 / 5) * 5),
            "Lean Kitchen (-15%)": lambda row: int(np.ceil(row["demand_estimate"] * 0.85 / 5) * 5),
            "Ex-Post Oracle (Upper Bound)": lambda row: row["demand_estimate"],
        }

        summary_rows = []
        for name, policy_fn in policies.items():
            tot_prep = 0
            tot_sold = 0
            tot_waste = 0
            tot_missed = 0
            tot_rev = 0.0
            tot_cost = 0.0
            tot_disp = 0.0
            tot_profit = 0.0
            tot_profit_regret = 0.0
            tot_waste_regret = 0.0
            stockouts = 0

            for _, row in daily_df.iterrows():
                d = row["demand_estimate"]
                q = policy_fn(row)
                p = row["selling_price"]
                c = row["cost"]

                eval_res = self.evaluate_decision(d, q, p, c)
                tot_prep += eval_res["portions_prepared"]
                tot_sold += eval_res["portions_sold"]
                tot_waste += eval_res["leftover_portions"]
                tot_missed += eval_res["missed_demand"]
                tot_rev += eval_res["revenue"]
                tot_cost += eval_res["ingredient_cost"]
                tot_disp += eval_res["waste_disposal_cost"]
                tot_profit += eval_res["estimated_profit"]
                tot_profit_regret += eval_res["profit_regret"]
                tot_waste_regret += eval_res["waste_regret"]
                stockouts += eval_res["stockout_flag"]

            n_records = len(daily_df)
            waste_rate = (tot_waste / tot_prep * 100.0) if tot_prep > 0 else 0.0
            stockout_rate = (stockouts / n_records * 100.0) if n_records > 0 else 0.0

            summary_rows.append({
                "policy_name": name,
                "total_portions_prepared": tot_prep,
                "total_portions_sold": tot_sold,
                "total_portions_wasted": tot_waste,
                "total_missed_demand": tot_missed,
                "waste_percentage": round(waste_rate, 2),
                "stockout_rate_pct": round(stockout_rate, 2),
                "total_revenue": round(tot_rev, 2),
                "total_cost": round(tot_cost + tot_disp, 2),
                "net_profit": round(tot_profit, 2),
                "total_profit_regret": round(tot_profit_regret, 2),
                "total_waste_regret": round(tot_waste_regret, 2),
            })

        return pd.DataFrame(summary_rows)
