"""MenuMind Synthetic Canteen Data Generator.

Transforms Kaggle Food Demand Forecasting dataset into realistic synthetic college-canteen
daily and weekly datasets suitable for demand forecasting, menu mix optimization, and
the MenuMind Rewind counterfactual food waste simulator.
"""

import sys
import os
import json
import random
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd
import numpy as np

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Ensure robust unicode output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from src.config import MenuMindConfig, parse_cli_args
from src.data_loader import RawDataLoader
from src.menu_mapper import MenuMapper
from src.academic_calendar import AcademicCalendar
from src.disaggregator import DemandDisaggregator
from src.kitchen_policy import KitchenSimulator
from src.validator import SyntheticDataValidator


def generate_canteen_dataset(cfg: MenuMindConfig) -> Dict[str, Any]:
    """Execute complete end-to-end synthetic dataset generation pipeline."""
    print("=" * 70)
    print("   MENUMIND: AI-POWERED CANTEEN MENU MIX OPTIMIZATION")
    print("   Synthetic Canteen Dataset Generation Pipeline")
    print("=" * 70)
    print(f"Random Seed:          {cfg.random_seed}")
    print(f"Start Date:           {cfg.start_date} ({cfg.num_weeks} weeks = {cfg.num_weeks * 7} operating days)")
    print(f"Source Center ID:     {cfg.center_id}")
    print(f"Demand Scaling:       {cfg.demand_scale}x (converting warehouse to college canteen volume)")
    print(f"Kitchen Policy:       {cfg.prep_policy} (Buffer: +{cfg.buffer_pct * 100:.0f}%, Batch: {cfg.kitchen_batch_size})")
    print(f"Waste Disposal Cost:  INR {cfg.waste_disposal_cost:.2f} per wasted portion")
    print(f"Output Directory:     {cfg.output_dir}")
    print("-" * 70)

    # Set seeds for deterministic reproducibility
    random.seed(cfg.random_seed)
    np.random.seed(cfg.random_seed)

    # 1. Load and merge raw source data
    print("\n[Step 1/6] Loading and auditing raw Kaggle dataset...")
    loader = RawDataLoader(raw_dir=cfg.raw_dir)
    center_data, meal_df, center_df, raw_audit = loader.load_and_merge(
        center_id=cfg.center_id,
        num_weeks=cfg.num_weeks,
        start_week=1,
    )
    print(f"  Loaded {len(center_data):,} records for Center {cfg.center_id} across {raw_audit['extracted_weeks']} weeks.")
    print(f"  Center Type: {raw_audit['center_type']} | Operating Area: {raw_audit['op_area']} sq km")

    # 2. Build Synthetic Catalog & Source Mapping
    print("\n[Step 2/6] Building synthetic menu catalog and source mapping...")
    mapper = MenuMapper(price_scale=cfg.price_scale)
    catalog_df, mapping_df = mapper.build_catalogs(center_data, meal_df)

    # If user wants a subset of items, select the top N by volume
    if cfg.num_items < len(catalog_df):
        keep_meals = mapping_df.sort_values(
            by="historical_mean_weekly_orders", ascending=False
        ).head(cfg.num_items)["original_meal_id"].values
        catalog_df = catalog_df[catalog_df["original_meal_id"].isin(keep_meals)].reset_index(drop=True)
        mapping_df = mapping_df[mapping_df["original_meal_id"].isin(keep_meals)].reset_index(drop=True)
        center_data = center_data[center_data["meal_id"].isin(keep_meals)].reset_index(drop=True)

    print(f"  Catalog ready: {len(catalog_df)} synthetic items across {catalog_df['category'].nunique()} categories.")

    # Create fast lookup dicts for items
    item_lookup = {r["original_meal_id"]: r for r in catalog_df.to_dict(orient="records")}

    # 3. Generate College Academic Calendar
    print("\n[Step 3/6] Generating college academic calendar and campus events...")
    calendar_engine = AcademicCalendar(start_date=cfg.start_date, num_weeks=cfg.num_weeks)
    calendar_df = calendar_engine.generate_calendar_days()
    calendar_by_week = calendar_df.groupby("week_number")
    print(f"  Calendar generated: {len(calendar_df)} operating days with holidays and campus events.")

    # 4. Disaggregation, Calendar Shocks, Kitchen Preparation & Accounting
    print("\n[Step 4/6] Disaggregating weekly demand & simulating kitchen operations...")
    disaggregator = DemandDisaggregator(
        demand_scale=cfg.demand_scale,
        promo_uplift=cfg.promo_uplift,
        random_seed=cfg.random_seed,
    )
    kitchen = KitchenSimulator(
        policy=cfg.prep_policy,
        buffer_pct=cfg.buffer_pct,
        batch_size=cfg.kitchen_batch_size,
        waste_disposal_cost=cfg.waste_disposal_cost,
        random_seed=cfg.random_seed,
    )

    daily_rows: List[Dict[str, Any]] = []
    disaggregation_audit: List[Dict[str, Any]] = []

    # Track item demand history per item for realistic kitchen forecasting
    item_demand_history: Dict[str, List[int]] = {row["item_id"]: [] for _, row in catalog_df.iterrows()}

    # Group raw center data by week
    weeks = sorted(center_data["week"].unique())

    for week_num in weeks:
        if week_num not in calendar_by_week.groups:
            continue

        week_calendar_days = calendar_by_week.get_group(week_num).sort_values("day_num").to_dict(orient="records")
        week_raw_items = center_data[center_data["week"] == week_num]

        for _, raw_row in week_raw_items.iterrows():
            meal_id = int(raw_row["meal_id"])
            if meal_id not in item_lookup:
                continue

            item_meta = item_lookup[meal_id]
            item_id = item_meta["item_id"]
            category = item_meta["category"]
            cuisine = item_meta["cuisine"]
            selling_price = item_meta["selling_price"]
            unit_cost = item_meta["cost"]
            calories = item_meta["calories"]
            base_rating = item_meta["base_rating"]
            elasticity = item_meta["price_elasticity"]

            # Scaled base weekly demand
            raw_orders = int(raw_row["num_orders"])
            scaled_weekly_orders = max(0, int(round(raw_orders * cfg.demand_scale)))

            # Step 4a: Preserving integer disaggregation into 7 days
            base_daily_shares = disaggregator.disaggregate_weekly_total(
                weekly_total=scaled_weekly_orders,
                category=category,
            )

            # Audit record for preservation check
            disaggregation_audit.append({
                "week_number": week_num,
                "meal_id": meal_id,
                "target_weekly_total": scaled_weekly_orders,
                "disaggregated_sum": int(np.sum(base_daily_shares)),
            })

            # Promotional signals from source data
            has_raw_promo = bool(
                raw_row.get("emailer_for_promotion", 0) == 1
                or raw_row.get("homepage_featured", 0) == 1
            )
            raw_checkout = float(raw_row.get("checkout_price", selling_price))
            raw_base = float(raw_row.get("base_price", selling_price))
            price_discount_ratio = max(0.0, (raw_base - raw_checkout) / raw_base) if raw_base > 0 else 0.0

            # Step 4b: Simulate daily demand & kitchen preparation for each day
            for day_dict in week_calendar_days:
                day_num = day_dict["day_num"]
                date_str = day_dict["date"]
                day_name = day_dict["day_of_week"]
                is_holiday = day_dict["is_holiday"]
                campus_event = day_dict["campus_event"]
                event_mult = day_dict["event_multipliers"].get(category, 1.0)

                base_d = base_daily_shares[day_num]

                # Promotions active during weekdays if source was promoted or on event days
                day_promo = has_raw_promo and (day_num in (0, 2, 4))  # Mon/Wed/Fri specials

                # Dynamic daily demand
                simulated_demand = disaggregator.compute_daily_demand_estimate(
                    base_daily_demand=base_d,
                    category=category,
                    is_promo=day_promo,
                    event_multiplier=event_mult,
                    price_elasticity=elasticity,
                    price_discount_ratio=price_discount_ratio,
                    student_rating=base_rating,
                )

                # Daily rating variation (Gaussian noise around baseline rating)
                daily_rating = round(
                    max(1.0, min(5.0, base_rating + random.gauss(0.0, 0.15))), 1
                )

                # Kitchen preparation decision
                history = item_demand_history[item_id]
                qty_prepared = kitchen.determine_preparation_quantity(
                    demand_estimate=simulated_demand,
                    item_history=history,
                    batch_size=cfg.kitchen_batch_size,
                )

                # Operational accounting identities
                accounting = kitchen.execute_daily_accounting(
                    demand_estimate=simulated_demand,
                    qty_prepared=qty_prepared,
                    selling_price=selling_price,
                    unit_cost=unit_cost,
                )

                # Update item history
                item_demand_history[item_id].append(simulated_demand)
                if len(item_demand_history[item_id]) > 14:
                    item_demand_history[item_id].pop(0)

                daily_rows.append({
                    "date": date_str,
                    "week_number": week_num,
                    "day_of_week": day_name,
                    "is_holiday": is_holiday,
                    "campus_event": campus_event,
                    "item_id": item_id,
                    "item_name": item_meta["item_name"],
                    "original_meal_id": meal_id,
                    "category": category,
                    "cuisine": cuisine,
                    "selling_price": selling_price,
                    "cost": unit_cost,
                    "calories": calories,
                    "rating": daily_rating,
                    "promotion": int(day_promo),
                    "demand_estimate": accounting["demand_estimate"],
                    "qty_prepared": accounting["qty_prepared"],
                    "qty_sold": accounting["qty_sold"],
                    "qty_wasted": accounting["qty_wasted"],
                    "stockout_flag": accounting["stockout_flag"],
                    "missed_demand": accounting["missed_demand"],
                    "revenue": accounting["revenue"],
                    "preparation_cost": accounting["preparation_cost"],
                    "waste_cost": accounting["waste_cost"],
                    "profit": accounting["profit"],
                })

    daily_df = pd.DataFrame(daily_rows)
    # Sort strictly by date, then item_id
    daily_df = daily_df.sort_values(by=["date", "item_id"]).reset_index(drop=True)

    # 5. Aggregate to Weekly Dataset
    print("\n[Step 5/6] Aggregating daily canteen operations to weekly summary...")
    weekly_agg = (
        daily_df.groupby(["week_number", "item_id", "item_name", "category", "cuisine", "original_meal_id"])
        .agg(
            days_offered=("date", "count"),
            demand_estimate=("demand_estimate", "sum"),
            qty_prepared=("qty_prepared", "sum"),
            qty_sold=("qty_sold", "sum"),
            qty_wasted=("qty_wasted", "sum"),
            missed_demand=("missed_demand", "sum"),
            stockout_days=("stockout_flag", "sum"),
            promotion_days=("promotion", "sum"),
            avg_selling_price=("selling_price", "mean"),
            avg_cost=("cost", "mean"),
            avg_rating=("rating", "mean"),
            revenue=("revenue", "sum"),
            preparation_cost=("preparation_cost", "sum"),
            waste_cost=("waste_cost", "sum"),
            profit=("profit", "sum"),
        )
        .reset_index()
    )

    weekly_agg["avg_selling_price"] = weekly_agg["avg_selling_price"].round(2)
    weekly_agg["avg_cost"] = weekly_agg["avg_cost"].round(2)
    weekly_agg["avg_rating"] = weekly_agg["avg_rating"].round(2)
    weekly_agg["revenue"] = weekly_agg["revenue"].round(2)
    weekly_agg["preparation_cost"] = weekly_agg["preparation_cost"].round(2)
    weekly_agg["waste_cost"] = weekly_agg["waste_cost"].round(2)
    weekly_agg["profit"] = weekly_agg["profit"].round(2)
    weekly_agg["waste_rate_pct"] = (
        (weekly_agg["qty_wasted"] / weekly_agg["qty_prepared"].replace(0, 1)) * 100.0
    ).round(2)

    # 6. Validate and Save Processed Files
    print("\n[Step 6/6] Executing comprehensive automated validation...")
    validator = SyntheticDataValidator(waste_disposal_cost=cfg.waste_disposal_cost)
    passed, validation_report = validator.run_all_checks(
        daily_df=daily_df,
        weekly_df=weekly_agg,
        catalog_df=catalog_df,
        mapping_df=mapping_df,
        disaggregation_audit=disaggregation_audit,
    )

    if not passed:
        print("\n[ERROR] Validation failed with the following issues:")
        for section, details in validation_report.items():
            if isinstance(details, dict) and not details.get("passed", True):
                print(f"  Section '{section}':")
                for msg in details.get("details", []):
                    print(f"    - {msg}")
        raise ValueError("Synthetic dataset generation aborted due to validation failures.")

    # Create output directory
    out_dir = Path(cfg.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    daily_path = out_dir / "synthetic_canteen_daily.csv"
    weekly_path = out_dir / "synthetic_canteen_weekly.csv"
    catalog_path = out_dir / "synthetic_menu_catalog.csv"
    mapping_path = out_dir / "source_mapping.csv"
    summary_path = out_dir / "generation_summary.json"

    daily_df.to_csv(daily_path, index=False)
    weekly_agg.to_csv(weekly_path, index=False)
    catalog_df.to_csv(catalog_path, index=False)
    mapping_df.to_csv(mapping_path, index=False)

    summary_content = {
        "generator_name": "MenuMind Synthetic Canteen Data Pipeline",
        "timestamp": pd.Timestamp.now().isoformat(),
        "configuration": cfg.to_dict(),
        "source_data_audit": raw_audit,
        "validation_results": validation_report,
        "files_generated": {
            "daily_dataset": str(daily_path.resolve()),
            "weekly_dataset": str(weekly_path.resolve()),
            "menu_catalog": str(catalog_path.resolve()),
            "source_mapping": str(mapping_path.resolve()),
            "summary_json": str(summary_path.resolve()),
        },
        "key_metrics": validation_report["summary"],
    }

    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary_content, f, indent=2)

    print("\n" + "=" * 70)
    print("   GENERATION & VALIDATION COMPLETED SUCCESSFULLY!")
    print("=" * 70)
    metrics = validation_report["summary"]
    print(f"Daily Records:       {metrics['daily_records_count']:,}")
    print(f"Weekly Records:      {metrics['weekly_records_count']:,}")
    print(f"Menu Items:          {metrics['unique_items_count']}")
    print(f"Date Range:          {metrics['date_range_start']} to {metrics['date_range_end']}")
    print(f"Total Prepared:      {metrics['total_prepared_portions']:,} portions")
    print(f"Total Sold:          {metrics['total_sold_portions']:,} portions")
    print(f"Total Wasted:        {metrics['total_wasted_portions']:,} portions")
    print(f"Waste Rate:          {metrics['waste_rate_percentage']}%")
    print(f"Stockout Rate:       {metrics['stockout_rate_percentage']}%")
    print(f"Total Revenue:       INR {metrics['total_gross_revenue']:,.2f}")
    print(f"Total Net Profit:    INR {metrics['total_net_profit']:,.2f}")
    print(f"\nGenerated files saved in: {out_dir.resolve()}")
    for k, v in summary_content["files_generated"].items():
        print(f"  - {k}: {v}")

    return summary_content


if __name__ == "__main__":
    config = parse_cli_args()
    generate_canteen_dataset(config)
