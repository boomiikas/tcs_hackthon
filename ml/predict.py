"""Inference and CLI prediction interface for CanteenIQ."""

import sys
import argparse
from pathlib import Path
import json

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Console encoding guard
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from ml import (
    predict_item_demand,
    predict_7_day_demand,
    calculate_preparation_quantity,
    generate_weekly_menu,
    analyze_food_waste,
    recommend_surplus_discounts,
    recommend_procurement,
    calculate_regret_metrics,
)


def main():
    parser = argparse.ArgumentParser(description="CanteenIQ ML Inference & Menu Optimization CLI")
    subparsers = parser.add_subparsers(dest="command", help="Operational command")

    # 1. Predict Single Date Demand
    pred_parser = subparsers.add_parser("predict", help="Predict item demand for a single future date")
    pred_parser.add_argument("--date", type=str, default="2025-12-15", help="Target service date YYYY-MM-DD")
    pred_parser.add_argument("--holiday", type=int, default=0, help="1 if holiday, 0 otherwise")
    pred_parser.add_argument("--promo", type=int, default=0, help="1 if promotional, 0 otherwise")
    pred_parser.add_argument("--json", action="store_true", help="Output raw JSON response")

    # 2. Predict 7-Day Demand Horizon
    pred7_parser = subparsers.add_parser("predict-7days", help="Generate 7-day forward forecasts for all dishes")
    pred7_parser.add_argument("--start-date", type=str, default="2025-12-15", help="Starting Monday date YYYY-MM-DD")
    pred7_parser.add_argument("--json", action="store_true", help="Output raw JSON")

    # 3. Plan Preparation
    prep_parser = subparsers.add_parser("plan-prep", help="Calculate recommended kitchen preparation quantity")
    prep_parser.add_argument("--item", type=str, default="Paneer Butter Masala Rice Bowl")
    prep_parser.add_argument("--demand", type=float, default=65.0)
    prep_parser.add_argument("--buffer", type=float, default=0.10)
    prep_parser.add_argument("--capacity", type=int, default=200)
    prep_parser.add_argument("--batch", type=int, default=5)

    # 4. Optimize Menu
    opt_parser = subparsers.add_parser("optimize-menu", help="Generate 7-day optimized menu mix")
    opt_parser.add_argument("--start-date", type=str, default="2025-12-15")
    opt_parser.add_argument("--budget", type=float, default=45000.0)
    opt_parser.add_argument("--capacity", type=int, default=800)
    opt_parser.add_argument("--min-dishes", type=int, default=8)
    opt_parser.add_argument("--max-dishes", type=int, default=14)
    opt_parser.add_argument("--json", action="store_true", help="Output raw JSON")

    # 5. Waste Audit
    waste_parser = subparsers.add_parser("audit-waste", help="Audit high-waste dishes and recommend actions")

    # 6. Regret Meter
    regret_parser = subparsers.add_parser("regret-meter", help="Calculate avoidable financial loss and 0-100 Regret Index")

    # 7. Surplus Discount Recommender
    surplus_parser = subparsers.add_parser("surplus", help="Recommend tiered surplus discounts and Mystery Meal bundle")
    surplus_parser.add_argument("--time", type=str, default="16:30", help="Current time HH:MM (e.g. 16:30)")
    surplus_parser.add_argument("--override", action="store_true", help="Manager safety manual confirmation override")

    # 8. Procurement Recommender
    proc_parser = subparsers.add_parser("procurement", help="Explode weekly menu into raw ingredient requirements & shortages")
    proc_parser.add_argument("--start-date", type=str, default="2025-12-15")

    args = parser.parse_args()

    if args.command == "predict":
        print(f"\n>>> Running Demand Forecast for Date: {args.date} (Holiday: {args.holiday}, Promo: {args.promo})")
        res = predict_item_demand(date=args.date, is_holiday=args.holiday, is_promotion=args.promo)
        if args.json:
            print(json.dumps(res, indent=2))
        else:
            print(f"Total Predicted Demand: {res['total_predicted_demand']} portions across {res['items_count']} dishes")
            print(f"Total Recommended Preparation: {res['total_recommended_preparation']} portions\n")
            print(f"{'Item Name':40s} | {'Cat':12s} | {'Pred':6s} | {'p10':5s} | {'p90':5s} | {'Prep':5s}")
            print("-" * 85)
            for it in res["predictions"][:12]:
                print(f"{it['item_name']:40s} | {it['category']:12s} | {it['predicted_demand']:6.1f} | {it['p10_pessimistic_demand']:5.1f} | {it['p90_surge_demand']:5.1f} | {it['recommended_preparation']:5d}")
            print(f"... and {len(res['predictions']) - 12} more dishes.")

    elif args.command == "predict-7days":
        print(f"\n>>> Generating 7-Day Forward Forecast starting {args.start_date}...")
        res = predict_7_day_demand(start_date=args.start_date)
        if args.json:
            print(json.dumps(res, indent=2))
        else:
            print(f"Horizon: {res['start_date']} to {res['end_date']}")
            print(f"Total 7-Day Forecast Demand: {res['total_forecast_demand']} portions")
            print(f"Total 7-Day Recommended Prep: {res['total_forecast_preparation']} portions\n")
            for day in res["daily_forecasts"]:
                print(f"  {day['day_of_week']:9s} ({day['date']}): {day['total_predicted_demand']:5.1f} demand portions | {day['total_recommended_preparation']:4d} prep portions")

    elif args.command == "plan-prep":
        print(f"\n>>> Planning Preparation for '{args.item}'")
        res = calculate_preparation_quantity(
            item_name=args.item,
            predicted_demand=args.demand,
            buffer_pct=args.buffer,
            kitchen_capacity=args.capacity,
            batch_multiple=args.batch,
        )
        print(f"  Predicted Demand:       {res['predicted_demand']} portions")
        print(f"  Buffer Applied:         +{res['buffer_percentage']}% ({res['buffer_portions']} extra portions)")
        print(f"  Recommended Prep:       {res['recommended_preparation']} portions")
        print(f"  Estimated Surplus:      {res['estimated_surplus']} portions")
        print(f"  Staged Cooking Batch 1: {res['staged_preparation']['batch_1_morning']} portions (Morning)")
        print(f"  Staged Cooking Batch 2: {res['staged_preparation']['batch_2_midday']} portions (Midday Review)")
        print(f"  Trigger Rule:           {res['staged_preparation']['batch_2_trigger_rule']}")

    elif args.command == "optimize-menu":
        print(f"\n>>> Generating 7-Day Optimized Menu Mix starting {args.start_date}...")
        res = generate_weekly_menu(
            start_date=args.start_date,
            daily_budget_inr=args.budget,
            daily_capacity_portions=args.capacity,
            min_dishes_per_day=args.min_dishes,
            max_dishes_per_day=args.max_dishes,
        )
        if args.json:
            print(json.dumps(res, indent=2))
        else:
            print("\n" + "=" * 70)
            print("   WEEKLY MENU MIX OPTIMIZATION RESULTS")
            print("=" * 70)
            comp = res["baseline_comparison"]
            print(f"AI Plan Net Profit:       INR {comp['ai_optimized_plan']['expected_net_profit']:,.2f}")
            print(f"Static Baseline Profit:   INR {comp['unoptimized_static_baseline']['expected_net_profit']:,.2f}")
            print(f"Contribution Uplift:      {comp['impact_improvements']['profit_increase_pct']}")
            print(f"Food Waste Reduction:     {comp['impact_improvements']['food_waste_reduction_pct']} ({comp['impact_improvements']['portions_saved_from_landfill']:,} portions saved!)")
            print(f"Waste Dollars Saved:      INR {comp['impact_improvements']['waste_cost_dollars_saved']:,.2f}")
            print(f"\nRationale:\n{res['selection_rationale']}\n")
            print(f"Sample Day 1 Menu ({res['daily_plans'][0]['day_of_week']} {res['daily_plans'][0]['date']}):")
            for it in res["daily_plans"][0]["menu_items"][:8]:
                print(f"  - {it['item_name']:35s} | Prep: {it['recommended_preparation']:3d} | Profit: INR {it['expected_profit']:,.2f}")

    elif args.command == "audit-waste":
        print("\n>>> Auditing Historical Waste and Generating Recommendations...")
        res = analyze_food_waste()
        kpis = res["waste_kpis"]
        print(f"Dishes Audited:                     {kpis['total_dishes_audited']}")
        print(f"Dishes Exceeding Waste Threshold:  {kpis['dishes_exceeding_waste_threshold']}")
        print(f"Total Waste Cost:                  INR {kpis['total_accumulated_waste_cost_inr']:,.2f}")
        print(f"Dishes Requiring Prep Reduction:   {kpis['dishes_requiring_prep_reduction']}")
        print(f"Dishes Requiring Prep Increase:    {kpis['dishes_requiring_prep_increase']}\n")
        print("Top 5 Dishes Recommended for Immediate Preparation Cut:")
        for it in res["action_recommendations"][:5]:
            print(f"  - {it['item_name']:35s} | Waste: {it['waste_rate_pct']:5.1f}% | Action: {it['action']}")

    elif args.command == "regret-meter":
        print("\n" + "=" * 70)
        print("   CANTEENIQ REGRET METER: AVOIDABLE FINANCIAL LOSS AUDIT")
        print("=" * 70)
        res = calculate_regret_metrics()
        audit_period = res.get("time_period_audited", {})
        print(f"Audit Horizon:                 {audit_period.get('description', 'Operational Dataset')}")
        print(f"Date Range:                    {audit_period.get('start_date', 'N/A')} to {audit_period.get('end_date', 'N/A')}")
        print(f"Regret Index Score:            {res['regret_index_score']}/100 ({res['status']})")
        print(f"Operational Efficiency Score:  {res['operational_efficiency_score']}/100")
        print(f"Full Dataset Avoidable Loss:   INR {res['total_avoidable_financial_loss_inr']:,.2f}")
        print(f"  - Over-prep Waste Regret:    INR {res['waste_regret_loss_inr']:,.2f} ({res['total_wasted_portions']:,} portions)")
        print(f"  - Under-prep Missed Margin:  INR {res['stockout_missed_margin_loss_inr']:,.2f} ({res['total_missed_demand_portions']:,} portions)")
        print(f"Total Realized Revenue:        INR {res['total_realized_revenue_inr']:,.2f}")
        if "daily_averages" in res:
            daily = res["daily_averages"]
            weekly = res["weekly_averages"]
            print("\nOperational Normalized Losses:")
            print(f"  - Daily Avoidable Loss:      INR {daily['daily_avoidable_loss_inr']:,.2f} / day")
            print(f"  - Weekly Avoidable Loss:     INR {weekly['weekly_avoidable_loss_inr']:,.2f} / week")
        print(f"\nManager Assessment:\n  {res['manager_assessment']}\n")

    elif args.command == "surplus":
        print(f"\n>>> Running Surplus Food Discount Engine (Time: {args.time})...")
        sample_surplus = [
            {"item_name": "Paneer Butter Masala Rice Bowl", "category": "Rice Bowl", "price": 268.53, "cost": 128.89, "surplus_portions": 12, "holding_time_hours": 2.5},
            {"item_name": "Classic Cold Hazelnut Mocha", "category": "Beverages", "price": 207.94, "cost": 91.49, "surplus_portions": 18, "holding_time_hours": 1.0},
            {"item_name": "Crispy Spring Rolls with Sweet Chili", "category": "Extras", "price": 171.61, "cost": 68.64, "surplus_portions": 14, "holding_time_hours": 2.0},
        ]
        res = recommend_surplus_discounts(sample_surplus, current_time_str=args.time, manager_safety_override=args.override)
        print(f"Applied Window:         {res['applied_discount_tier']} (-{res['discount_percentage']}%)")
        print(f"Potential Revenue Saved: INR {res['total_potential_recovery_revenue_inr']:,.2f}")
        print(f"Disposal Fees Avoided:  INR {res['total_disposal_costs_avoided_inr']:,.2f}")
        print(f"Total Value Salvaged:   INR {res['total_financial_value_salvaged_inr']:,.2f}\n")
        print("Discounted Items for Clearance:")
        for it in res["discounted_items"]:
            print(f"  - {it['item_name']:35s} | Original: INR {it['original_price_inr']} -> Discounted: INR {it['discounted_price_inr']} | Surplus: {it['surplus_portions']}")
        mb = res["mystery_meal_bundle"]
        if mb.get("available"):
            print(f"\n{mb['bundle_title']}:")
            print(f"  Bundled Items:  {', '.join(mb['bundled_items'])}")
            print(f"  Rescue Price:   INR {mb['rescue_combo_price_inr']} (-{mb['mystery_discount_pct']}%)")
            print(f"  Combos Ready:   {mb['max_combos_packable']} combos ({mb['total_portions_rescued']} portions rescued)")

    elif args.command == "procurement":
        print(f"\n>>> Calculating Raw Ingredient Procurement Demands for Week starting {args.start_date}...")
        res = recommend_procurement(start_date=args.start_date)
        print(f"Total Portions Planned:           {res['total_weekly_portions_planned']}")
        print(f"Distinct Ingredients Required:    {res['distinct_ingredients_required']}")
        print(f"Critical Stockout Shortages:      {res['critical_shortages_count']}")
        print(f"Overstock Spoilage Risks:         {res['spoilage_risks_count']}\n")
        print("Top Projected Stockout Shortages (Reorder Immediately):")
        for sh in res["projected_shortages"][:4]:
            print(f"  [SHORTAGE] {sh['ingredient']:25s} | Stock: {sh['current_stock']:5.1f} {sh['unit']} | Needed: {sh['required_for_menu']:5.1f} {sh['unit']} | Deficit: {sh['deficit_to_order']:5.1f} {sh['unit']}")
        if res["projected_overstock_risks"]:
            print("\nProjected Overstock / Spoilage Risks:")
            for ov in res["projected_overstock_risks"]:
                print(f"  [OVERSTOCK] {ov['ingredient']:25s} | Stock: {ov['current_stock']:5.1f} vs Needed: {ov['weekly_requirement']:5.1f} | {ov['risk_warning']}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
