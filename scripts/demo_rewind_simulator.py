"""Demo of MenuMind Rewind: The Counterfactual Food Waste Simulator.

Demonstrates retrospective counterfactual simulations on the generated synthetic dataset,
evaluating alternative preparation decisions, waste reduction, and regret metrics.
"""

import sys
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Ensure robust unicode output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from src.rewind_engine import MenuMindRewindSimulator


def run_rewind_demo():
    print("=" * 70)
    print("   MENUMIND REWIND: THE COUNTERFACTUAL FOOD WASTE SIMULATOR")
    print("=" * 70)

    daily_path = Path("data/processed/synthetic_canteen_daily.csv")
    if not daily_path.exists():
        print(f"[ERROR] '{daily_path}' not found. Please run the generation script first.")
        sys.exit(1)

    daily_df = pd.read_csv(daily_path)
    simulator = MenuMindRewindSimulator(waste_disposal_cost=2.0)

    # 1. Macro Retrospective Policy Comparison across entire academic year
    print("\n[Analysis 1] Retrospective Policy Comparison (Full Academic Year):")
    print("-" * 70)
    policy_comparison = simulator.compare_retrospective_policies(daily_df)
    cols_to_show = [
        "policy_name",
        "total_portions_prepared",
        "total_portions_sold",
        "total_portions_wasted",
        "waste_percentage",
        "stockout_rate_pct",
        "net_profit",
        "total_waste_regret",
    ]
    print(policy_comparison[cols_to_show].to_string(index=False))

    # Calculate AI food waste reduction vs Chef
    chef_waste = policy_comparison.loc[
        policy_comparison["policy_name"] == "Actual Simulated Chef", "total_portions_wasted"
    ].values[0]
    ai_waste = policy_comparison.loc[
        policy_comparison["policy_name"] == "MenuMind AI Recommendation", "total_portions_wasted"
    ].values[0]
    waste_saved = chef_waste - ai_waste
    waste_reduction_pct = (waste_saved / chef_waste) * 100.0

    chef_profit = policy_comparison.loc[
        policy_comparison["policy_name"] == "Actual Simulated Chef", "net_profit"
    ].values[0]
    ai_profit = policy_comparison.loc[
        policy_comparison["policy_name"] == "MenuMind AI Recommendation", "net_profit"
    ].values[0]
    profit_gain = ai_profit - chef_profit

    print("\n" + "=" * 70)
    print("   REWIND IMPACT SUMMARY:")
    print(f"   Food Waste Reduced:   {waste_saved:,} portions ({waste_reduction_pct:.1f}% reduction!)")
    print(f"   Net Profit Gain:      +INR {profit_gain:,.2f}")
    print("=" * 70)

    # 2. Micro Item-Level Quantity Sweep on a High-Volume Day
    sample_day = daily_df[
        (daily_df["campus_event"] == "Annual Cultural Fest") & (daily_df["demand_estimate"] > 30)
    ].iloc[0]

    date = sample_day["date"]
    item_id = sample_day["item_id"]
    item_name = sample_day["item_name"]
    demand = int(sample_day["demand_estimate"])
    actual_prep = int(sample_day["qty_prepared"])
    price = float(sample_day["selling_price"])
    cost = float(sample_day["cost"])

    print(f"\n[Analysis 2] Counterfactual Quantity Sweep on Event Day ({date}):")
    print(f"Item: {item_name} ({item_id}) | Realized Demand: {demand} portions | Selling Price: INR {price} | Cost: INR {cost}")
    print(f"Chef Actually Prepared: {actual_prep} portions\n")

    sweep_df = simulator.simulate_quantity_sweep(
        date=date,
        item_id=item_id,
        item_name=item_name,
        demand=demand,
        actual_prepared=actual_prep,
        selling_price=price,
        unit_cost=cost,
        step=5,
        range_padding=20,
    )

    display_cols = [
        "portions_prepared",
        "portions_sold",
        "leftover_portions",
        "missed_demand",
        "estimated_profit",
        "waste_regret",
        "missed_demand_regret",
        "profit_regret",
        "is_actual_decision",
        "is_oracle_optimal",
    ]
    print(sweep_df[display_cols].to_string(index=False))


if __name__ == "__main__":
    run_rewind_demo()
