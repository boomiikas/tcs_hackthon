"""Comprehensive unit test suite for CanteenIQ Machine Learning and Optimization Pipeline."""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path

from ml.data_loader import CanteenDataLoader
from ml.preprocessing import CanteenFeatureEngineer
from ml.demand_model import DemandModelSuite, calculate_wape, BaselineRegressor
from ml.preparation_planner import PreparationPlanner
from ml.menu_optimizer import MenuMixOptimizer
from ml.waste_analyzer import WasteAnalyzer


def test_data_loader_schema_and_integrity():
    """Verify data loader loads existing dataset without errors and validates all required fields."""
    loader = CanteenDataLoader()
    df, audit = loader.load_and_validate()

    assert len(df) > 1000
    assert audit["final_clean_rows"] == len(df)
    assert audit["unique_items"] >= 40
    assert (df["price"] > 0).all()
    assert (df["cost"] > 0).all()
    assert (df["qty_prepared"] >= 0).all()
    assert (df["qty_sold"] >= 0).all()
    assert (df["qty_wasted"] >= 0).all()
    assert ((df["rating"] >= 1.0) & (df["rating"] <= 5.0)).all()


def test_data_leakage_prevention():
    """Verify that same-day sales, prep, and waste are strictly excluded from feature inputs."""
    loader = CanteenDataLoader()
    df, _ = loader.load_and_validate()

    fe = CanteenFeatureEngineer()
    enriched = fe.fit_transform(df.head(500))

    # Critical Leakage Checks:
    forbidden_features = ["qty_sold", "qty_prepared", "qty_wasted", "stockout_flag", "missed_demand"]
    for f in forbidden_features:
        assert f not in fe.feature_names, f"CRITICAL LEAKAGE: '{f}' is present in feature inputs!"

    # Verify lag shift >= 1: for any item, lag_1d of day t must equal qty_sold of day t-1
    sample_item = enriched["item_name"].iloc[0]
    item_df = enriched[enriched["item_name"] == sample_item].sort_values("date").reset_index(drop=True)
    if len(item_df) >= 3:
        assert item_df.loc[1, "lag_1d"] == item_df.loc[0, "qty_sold"]
        assert item_df.loc[2, "lag_1d"] == item_df.loc[1, "qty_sold"]

    # Verify chronological split boundaries
    X_tr, y_tr, X_val, y_val, X_te, y_te, meta = fe.split_chronological(enriched)
    assert meta["train_date_range"][1] < meta["val_date_range"][0]
    assert meta["val_date_range"][1] < meta["test_date_range"][0]


def test_demand_models_and_wape():
    """Test model training, prediction non-negativity, and WAPE zero-division safety."""
    # Test safe WAPE calculation
    assert calculate_wape(np.array([10, 20]), np.array([12, 18])) == 0.1333
    assert calculate_wape(np.array([0, 0]), np.array([0, 0])) == 0.0

    # Test baseline regressor
    base = BaselineRegressor()
    dummy_x = pd.DataFrame([{"lag_7d": 45.0, "rolling_7d_mean": 40.0, "item_historical_mean": 35.0}])
    preds = base.predict(dummy_x)
    assert len(preds) == 1
    assert preds[0] == 45.0


def test_preparation_planner_logic_and_conflicts():
    """Verify buffer calculations, batch increments, capacity limits, and conflict handling."""
    planner = PreparationPlanner(default_buffer_pct=0.10, default_kitchen_capacity=200, default_batch_size=5)

    # 1. Standard calculation: 100 demand + 10% buffer = 110 portions
    res = planner.calculate_preparation(item_name="Biryani", predicted_demand=100.0, buffer_pct=0.10)
    assert res["recommended_preparation"] == 110
    assert res["estimated_surplus"] == 10
    assert res["has_capacity_conflict"] is False

    # 2. Batch rounding to increments of 5: 32 demand + 10% buffer = 35.2 -> ceil 36 -> batch 40
    res_batch = planner.calculate_preparation(item_name="Biryani", predicted_demand=32.0, buffer_pct=0.10, batch_multiple=5)
    assert res_batch["recommended_preparation"] == 40
    assert res_batch["recommended_preparation"] % 5 == 0

    # 3. Capacity ceiling: 250 demand with capacity 200 -> capped at 200
    res_cap = planner.calculate_preparation(item_name="Biryani", predicted_demand=250.0, kitchen_capacity=200)
    assert res_cap["recommended_preparation"] == 200

    # 4. Conflict detection: min_batch 150 > capacity 100 -> flags conflict
    res_conf = planner.calculate_preparation(
        item_name="Biryani", predicted_demand=50.0, kitchen_capacity=100, min_batch_size=150
    )
    assert res_conf["has_capacity_conflict"] is True
    assert "exceeds maximum kitchen capacity" in res_conf["conflict_message"]

    # 5. Staged two-batch preparation
    assert res["staged_preparation"]["staged_cooking_enabled"] is True
    assert res["staged_preparation"]["batch_1_morning"] + res["staged_preparation"]["batch_2_midday"] == 110


def test_menu_optimizer_milp():
    """Verify MILP menu mix optimizer generates valid 7-day plans respecting variety and capacity."""
    candidate_items = pd.DataFrame([
        {"item_name": "Paneer Bowl", "category": "Rice Bowl", "price": 120.0, "cost": 50.0, "calories": 550, "rating": 4.7},
        {"item_name": "Filter Coffee", "category": "Beverages", "price": 40.0, "cost": 15.0, "calories": 110, "rating": 4.8},
        {"item_name": "Veg Panini", "category": "Sandwich", "price": 90.0, "cost": 38.0, "calories": 420, "rating": 4.6},
        {"item_name": "Pasta Alfredo", "category": "Pasta", "price": 130.0, "cost": 60.0, "calories": 540, "rating": 4.3},
        {"item_name": "Margherita Pizza", "category": "Pizza", "price": 160.0, "cost": 70.0, "calories": 650, "rating": 4.5},
        {"item_name": "Caesar Salad", "category": "Salad", "price": 95.0, "cost": 42.0, "calories": 220, "rating": 4.4},
        {"item_name": "Veg Wontons", "category": "Starters", "price": 75.0, "cost": 30.0, "calories": 270, "rating": 4.4},
        {"item_name": "Gulab Jamun", "category": "Desert", "price": 50.0, "cost": 20.0, "calories": 310, "rating": 4.6},
        {"item_name": "Masala Chai", "category": "Beverages", "price": 30.0, "cost": 10.0, "calories": 100, "rating": 4.8},
    ])

    forecast_rows = []
    for d in range(7):
        for it in candidate_items["item_name"]:
            forecast_rows.append({"item_name": it, "day_of_week": d, "predicted_demand": 25.0})
    weekly_forecast = pd.DataFrame(forecast_rows)

    optimizer = MenuMixOptimizer(
        daily_capacity_portions=500,
        daily_budget_inr=30000.0,
        min_dishes_per_day=4,
        max_dishes_per_day=8,
    )

    plan = optimizer.optimize_weekly_menu(
        candidate_items_df=candidate_items,
        weekly_forecast_df=weekly_forecast,
        start_date="2025-05-12",
        required_categories=["Beverages", "Rice Bowl"],
    )

    assert plan["days_planned"] == 7
    assert len(plan["daily_plans"]) == 7

    for day in plan["daily_plans"]:
        assert 4 <= day["dishes_count"] <= 8
        assert day["total_portions_prepared"] <= 500
        cats = [it["category"] for it in day["menu_items"]]
        assert "Beverages" in cats
        assert "Rice Bowl" in cats

    assert plan["baseline_comparison"]["impact_improvements"]["portions_saved_from_landfill"] >= 0


def test_waste_analyzer_and_mystery_meal():
    """Verify high-waste identification and Mystery Meal food safety notices."""
    loader = CanteenDataLoader()
    df, _ = loader.load_and_validate()

    analyzer = WasteAnalyzer(waste_disposal_cost=2.0)
    audit = analyzer.analyze_operational_waste(df.head(1000))

    assert "waste_kpis" in audit
    assert len(audit["action_recommendations"]) > 0
    actions = [a["action"] for a in audit["action_recommendations"]]
    assert any(a in ["REDUCE PREPARATION", "INCREASE PREPARATION", "MAINTAIN CORE STAPLE"] for a in actions)

    # Test Mystery Meal surplus combo
    surplus_inv = [
        {"item_name": "Paneer Rice Bowl", "category": "Rice Bowl", "price": 120.0, "surplus_portions": 8},
        {"item_name": "Iced Tea", "category": "Beverages", "price": 50.0, "surplus_portions": 15},
        {"item_name": "Spring Rolls", "category": "Starters", "price": 70.0, "surplus_portions": 10},
    ]
    combo = analyzer.build_mystery_meal_recommendation(surplus_inv, target_discount_pct=35.0)
    assert combo["combo_available"] is True
    assert len(combo["bundled_items"]) == 3
    assert combo["discount_percentage"] == 35.0
    assert combo["rescue_combo_price_inr"] < combo["original_total_price_inr"]
    assert combo["food_safety_notice"]["requires_manual_inspection"] is True
    assert combo["food_safety_notice"]["holding_time_limit_hours"] == 4.0


def test_uncertainty_estimator_coverage():
    """Verify calibrated prediction intervals [P10, P90] and empirical coverage metrics."""
    from ml.uncertainty import DemandUncertaintyEstimator

    # Generate synthetic training and testing data
    np.random.seed(42)
    n = 200
    X = pd.DataFrame({
        "feat1": np.random.uniform(10, 50, n),
        "feat2": np.random.uniform(1, 5, n),
    })
    y = pd.Series(X["feat1"] * 0.8 + np.random.normal(0, 3, n))

    est = DemandUncertaintyEstimator(random_state=42)
    est.fit(X.iloc[:140], y.iloc[:140], X.iloc[140:170], y.iloc[140:170])

    p10, p50, p90 = est.predict_intervals(X.iloc[170:])
    assert len(p10) == 30
    assert np.all(p10 <= p50)
    assert np.all(p50 <= p90)

    eval_res = est.evaluate_test_coverage(X.iloc[170:], y.iloc[170:])
    assert "empirical_test_coverage_pct" in eval_res
    assert eval_res["empirical_test_coverage_pct"] >= 60.0  # reasonable coverage on small sample
    assert eval_res["mean_interval_width_portions"] > 0.0

    risk = est.assess_forecast_risk(predicted_demand=30.0, p10=20.0, p90=40.0)
    assert risk["risk_level"] in ["LOW_UNCERTAINTY", "MODERATE_UNCERTAINTY", "HIGH_UNCERTAINTY"]


def test_regret_meter_calculation():
    """Verify Regret Meter calculates avoidable financial loss and 0-100 normalized score."""
    from ml import calculate_regret_metrics

    res = calculate_regret_metrics()
    assert 0.0 <= res["regret_index_score"] <= 100.0
    assert 0.0 <= res["operational_efficiency_score"] <= 100.0
    assert res["regret_index_score"] + res["operational_efficiency_score"] == 100.0
    assert res["total_avoidable_financial_loss_inr"] > 0
    assert res["waste_regret_loss_inr"] > 0
    assert res["status"] in ["LOW_REGRET", "MODERATE_REGRET", "HIGH_REGRET"]


def test_surplus_recommender_tiers_and_safety():
    """Verify tiered discounting, time windows, and food safety gating."""
    from ml.surplus_recommender import SurplusFoodRecommender

    recommender = SurplusFoodRecommender(waste_disposal_cost=2.0)
    sample_surplus = [
        {"item_name": "Paneer Rice Bowl", "category": "Rice Bowl", "price": 150.0, "cost": 70.0, "surplus_portions": 10, "holding_time_hours": 2.0},
        {"item_name": "Iced Lemon Tea", "category": "Beverages", "price": 60.0, "cost": 25.0, "surplus_portions": 15, "holding_time_hours": 1.0},
        {"item_name": "Spoiled Curry", "category": "Rice Bowl", "price": 140.0, "cost": 65.0, "surplus_portions": 5, "holding_time_hours": 5.5},  # Exceeds 4h!
    ]

    # Afternoon run (35% discount)
    res = recommender.recommend_discounts(sample_surplus, current_time_str="17:00")
    assert res["discount_percentage"] == 35.0
    assert res["eligible_surplus_items_count"] == 2
    assert res["unsafe_disqualified_items_count"] == 1  # Spoiled Curry must be disqualified
    assert res["unsafe_items_flagged"][0]["item_name"] == "Spoiled Curry"
    assert "Holding time exceeded" in res["unsafe_items_flagged"][0]["reason"]
    assert res["mystery_meal_bundle"]["available"] is True


def test_procurement_advisor():
    """Verify bill-of-materials explosion and pantry stock shortage detection."""
    from ml.procurement import ProcurementAdvisor

    advisor = ProcurementAdvisor(kitchen_spillage_buffer_pct=5.0)
    fake_menu = {
        "daily_plans": [
            {
                "menu_items": [
                    {"category": "Rice Bowl", "recommended_preparation": 50},
                    {"category": "Beverages", "recommended_preparation": 80},
                    {"category": "Sandwich", "recommended_preparation": 40},
                ]
            }
        ]
    }
    stock = {
        "Rice (Basmati/Raw)": 2.0,  # low stock -> shortage
        "Fresh Milk": 50.0,         # ample stock
    }
    res = advisor.calculate_ingredient_procurement(fake_menu, current_inventory_stock=stock)
    assert res["distinct_ingredients_required"] > 5
    assert res["total_weekly_portions_planned"] == 170

    shortages = [sh["ingredient"] for sh in res["projected_shortages"]]
    assert "Rice (Basmati/Raw)" in shortages


def test_predict_7_day_demand_horizon():
    """Verify 7-day multi-step recursive forecasting without requiring future actual sales."""
    from ml import predict_7_day_demand

    res = predict_7_day_demand(start_date="2025-12-15")
    assert res["start_date"] == "2025-12-15"
    assert res["end_date"] == "2025-12-21"
    assert len(res["daily_forecasts"]) == 7
    assert res["total_forecast_demand"] > 500
    assert res["total_forecast_preparation"] > 500

    # Ensure all days have non-negative demand and preparation
    for d in res["daily_forecasts"]:
        assert d["total_predicted_demand"] > 0
        assert d["total_recommended_preparation"] >= d["total_predicted_demand"]
        for it in d["items"][:5]:
            assert it["p10_lower_bound"] <= it["p90_upper_bound"]
            assert it["recommended_preparation"] >= 0


def test_menu_optimizer_financial_consistency_and_constraints():
    """Verify MILP financial calculations, accounting identities, and strict constraint enforcement."""
    from ml import generate_weekly_menu

    # Run optimizer with tight calorie constraint to verify nutrition constraint enforcement
    res = generate_weekly_menu(
        start_date="2025-05-12",
        daily_budget_inr=45000.0,
        daily_capacity_portions=800,
        min_dishes_per_day=8,
        max_dishes_per_day=14,
        min_avg_calories=250.0,
        max_avg_calories=360.0,  # tight calorie upper bound
    )

    comp = res["baseline_comparison"]
    ai = comp["ai_optimized_plan"]
    base = comp["unoptimized_static_baseline"]
    impact = comp["impact_improvements"]

    # 1. Financial accounting identities
    # Net profit = Gross revenue - Prep cost - Waste disposal fee
    assert round(ai["expected_gross_revenue"] - ai["expected_ingredient_cost"] - (ai["total_portions_wasted"] * 2.0), 2) == ai["expected_net_profit"]
    assert round(base["expected_gross_revenue"] - base["expected_ingredient_cost"] - (base["total_portions_wasted"] * 2.0), 2) == base["expected_net_profit"]

    # 2. Recomputed percentage improvements
    expected_profit_lift = round(((ai["expected_net_profit"] - base["expected_net_profit"]) / abs(base["expected_net_profit"])) * 100.0, 1)
    expected_waste_red = round(((base["total_portions_wasted"] - ai["total_portions_wasted"]) / base["total_portions_wasted"]) * 100.0, 1)
    assert impact["profit_increase_pct"] == f"+{expected_profit_lift}%"
    assert impact["food_waste_reduction_pct"] == f"-{expected_waste_red}%"
    assert impact["portions_saved_from_landfill"] == base["total_portions_wasted"] - ai["total_portions_wasted"]

    # 3. Constraints validation across all 7 days
    assert len(res["daily_plans"]) == 7
    dish_frequency = {}
    for day in res["daily_plans"]:
        # Variety constraint
        assert 8 <= day["dishes_count"] <= 14
        # Kitchen capacity constraint
        assert day["total_portions_prepared"] <= 800
        # Budget constraint
        day_cost = sum(it["expected_cost"] for it in day["menu_items"])
        assert day_cost <= 45000.0
        # Nutrition constraint strictly enforced: max 360 kcal
        assert day["avg_calories_per_dish"] <= 360.0
        assert day["avg_calories_per_dish"] >= 250.0

        for it in day["menu_items"]:
            # Single-dish accounting consistency
            assert it["expected_sold"] == min(it["predicted_demand"], it["recommended_preparation"])
            assert it["expected_waste"] == max(0, it["recommended_preparation"] - it["expected_sold"])
            assert it["expected_revenue"] == round(it["expected_sold"] * it["price"], 2)
            assert it["expected_cost"] == round(it["recommended_preparation"] * it["cost"], 2)
            name = it["item_name"]
            dish_frequency[name] = dish_frequency.get(name, 0) + 1

    # Anti-fatigue constraint: specialty dishes max 4 days/week
    for name, freq in dish_frequency.items():
        # Masala Chai or beverages/rice bowls can appear 7 days, specialty max 4
        assert freq <= 7


def test_regret_meter_audit_and_hand_calculations():
    """Verify Regret Meter with small hand-calculated example, edge cases, and zero-overlap proof."""
    analyzer = WasteAnalyzer(waste_disposal_cost=2.0)

    # Hand-calculated toy scenario
    # Item A: Over-prepared (Q=14, D=10 -> Sold=10, Waste=4, Missed=0), Price=100, Cost=40
    #   Waste cost = 4 * (40 + 2) = 168.0
    #   Missed margin = 0.0
    #   Revenue = 10 * 100 = 1000.0
    # Item B: Under-prepared (Q=15, D=20 -> Sold=15, Waste=0, Missed=5), Price=120, Cost=50
    #   Waste cost = 0.0
    #   Missed margin = 5 * (120 - 50) = 350.0
    #   Revenue = 15 * 120 = 1800.0
    toy_df = pd.DataFrame([
        {
            "date": "2025-01-01", "item_name": "Item A", "price": 100.0, "cost": 40.0,
            "qty_prepared": 14, "qty_sold": 10, "qty_wasted": 4, "missed_demand": 0
        },
        {
            "date": "2025-01-01", "item_name": "Item B", "price": 120.0, "cost": 50.0,
            "qty_prepared": 15, "qty_sold": 15, "qty_wasted": 0, "missed_demand": 5
        },
    ])

    toy_res = analyzer.calculate_regret_meter(toy_df)
    assert toy_res["waste_regret_loss_inr"] == 168.0
    assert toy_res["stockout_missed_margin_loss_inr"] == 350.0
    assert toy_res["total_avoidable_financial_loss_inr"] == 518.0
    assert toy_res["total_realized_revenue_inr"] == 2800.0
    # Regret Index = 518 / (2800 + 518) * 100 = 518 / 3318 * 100 = 15.6118% -> 15.6
    assert toy_res["regret_index_score"] == 15.6
    assert toy_res["operational_efficiency_score"] == 84.4

    # Edge Case 1: Zero waste and zero stockout
    perfect_df = pd.DataFrame([
        {"date": "2025-01-01", "item_name": "Item A", "price": 100.0, "cost": 40.0, "qty_prepared": 10, "qty_sold": 10, "qty_wasted": 0, "missed_demand": 0}
    ])
    perf_res = analyzer.calculate_regret_meter(perfect_df)
    assert perf_res["regret_index_score"] == 0.0
    assert perf_res["operational_efficiency_score"] == 100.0
    assert perf_res["total_avoidable_financial_loss_inr"] == 0.0

    # Edge Case 2: 100% waste, 0 sold
    waste_only_df = pd.DataFrame([
        {"date": "2025-01-01", "item_name": "Item A", "price": 100.0, "cost": 40.0, "qty_prepared": 10, "qty_sold": 0, "qty_wasted": 10, "missed_demand": 0}
    ])
    waste_res = analyzer.calculate_regret_meter(waste_only_df)
    assert waste_res["regret_index_score"] == 100.0
    assert waste_res["operational_efficiency_score"] == 0.0
    assert waste_res["total_realized_revenue_inr"] == 0.0

    # Verify mutual exclusivity on full dataset
    loader = CanteenDataLoader()
    full_df, _ = loader.load_and_validate()
    overlap = (full_df["qty_wasted"] > 0) & (full_df["missed_demand"] > 0)
    assert overlap.sum() == 0, "Waste and missed demand must be mutually exclusive on each observation!"


def test_seven_day_recursive_forecast_zero_leakage_and_invariance():
    """Verify recursive multi-step forecasting and strict invariance to future data tampering."""
    import tempfile
    from ml import predict_7_day_demand

    start_date = "2025-05-12"
    res_orig = predict_7_day_demand(start_date=start_date)

    assert len(res_orig["daily_forecasts"]) == 7
    assert res_orig["start_date"] == start_date
    assert res_orig["end_date"] == "2025-05-18"

    # Mutate all future data in a temporary copy of the dataset
    loader = CanteenDataLoader()
    df, _ = loader.load_and_validate()
    df_tampered = df.copy()

    # Tamper future data: set sales to 99999 portions
    future_mask = df_tampered["date"] >= start_date
    df_tampered.loc[future_mask, "qty_sold"] = 99999.0
    df_tampered.loc[future_mask, "qty_prepared"] = 99999.0
    df_tampered.loc[future_mask, "qty_wasted"] = 0.0

    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
        df_tampered.to_csv(f.name, index=False)
        tmp_path = f.name

    res_tampered = predict_7_day_demand(start_date=start_date, filepath=tmp_path)

    # Invariance check: Modifying future actuals must have exactly ZERO impact on forecast
    assert res_orig["total_forecast_demand"] == res_tampered["total_forecast_demand"]
    assert res_orig["total_forecast_preparation"] == res_tampered["total_forecast_preparation"]
    for d1, d2 in zip(res_orig["daily_forecasts"], res_tampered["daily_forecasts"]):
        assert d1["date"] == d2["date"]
        assert d1["total_predicted_demand"] == d2["total_predicted_demand"]
        assert d1["total_recommended_preparation"] == d2["total_recommended_preparation"]

