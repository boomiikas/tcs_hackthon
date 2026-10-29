"""CanteenIQ Machine Learning, Demand Forecasting & Menu Mix Optimization Engine.

Clean unified Python interface for FastAPI backend integration and CLI workflows.
"""

from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from pathlib import Path
import joblib

from ml.data_loader import CanteenDataLoader, load_and_validate_data
from ml.preprocessing import CanteenFeatureEngineer
from ml.eda import CanteenEDA
from ml.demand_model import DemandModelSuite
from ml.uncertainty import DemandUncertaintyEstimator
from ml.preparation_planner import PreparationPlanner
from ml.menu_optimizer import MenuMixOptimizer
from ml.waste_analyzer import WasteAnalyzer
from ml.surplus_recommender import SurplusFoodRecommender
from ml.procurement import ProcurementAdvisor
from ml.schemas import (
    DemandPredictionRequest,
    DemandPredictionResponse,
    PreparationCalculationRequest,
    PreparationCalculationResponse,
    MenuOptimizationRequest,
    MenuOptimizationResponse,
    MysteryMealRequest,
    MysteryMealResponse,
    SevenDayForecastRequest,
    SevenDayForecastResponse,
    RegretMeterResponse,
    SurplusDiscountResponse,
    ProcurementResponse,
)

__version__ = "1.0.0"
__all__ = [
    "load_and_validate_data",
    "train_demand_model",
    "evaluate_demand_model",
    "predict_item_demand",
    "predict_7_day_demand",
    "calculate_preparation_quantity",
    "generate_weekly_menu",
    "analyze_food_waste",
    "recommend_surplus_discounts",
    "recommend_procurement",
    "calculate_regret_metrics",
]


def train_demand_model(
    filepath: Optional[str] = None,
    save_artifacts: bool = True,
    artifact_path: str = "ml/artifacts/demand_model.joblib",
) -> Dict[str, Any]:
    """Train baseline, Random Forest, and HistGradientBoosting models, selecting the best via validation."""
    loader = CanteenDataLoader(filepath=filepath)
    clean_df, audit = loader.load_and_validate()

    fe = CanteenFeatureEngineer()
    enriched_df = fe.fit_transform(clean_df)

    X_train, y_train, X_val, y_val, X_test, y_test, split_meta = fe.split_chronological(enriched_df)

    # Context for per-item evaluation
    test_context = enriched_df[enriched_df["date"] >= split_meta["test_date_range"][0]]

    suite = DemandModelSuite(random_state=42)
    eval_results = suite.train_and_evaluate_all(
        X_train=X_train,
        y_train=y_train,
        X_val=X_val,
        y_val=y_val,
        X_test=X_test,
        y_test=y_test,
        test_df_context=test_context,
    )

    # Train and calibrate uncertainty estimator
    uncertainty_est = DemandUncertaintyEstimator(random_state=42)
    uncertainty_est.fit(X_train, y_train, X_val, y_val)
    uncertainty_eval = uncertainty_est.evaluate_test_coverage(X_test, y_test)
    eval_results["uncertainty_evaluation"] = uncertainty_eval

    saved_path = None
    if save_artifacts:
        saved_path = suite.save_artifacts(filepath=artifact_path)
        fe_path = str(Path(artifact_path).parent / "feature_engineer.joblib")
        joblib.dump(fe, fe_path)
        unc_path = str(Path(artifact_path).parent / "uncertainty_estimator.joblib")
        joblib.dump(uncertainty_est, unc_path)

    return {
        "audit": audit,
        "split_metadata": split_meta,
        "evaluation": eval_results,
        "artifact_saved_to": saved_path,
    }


def evaluate_demand_model(
    artifact_path: str = "ml/artifacts/demand_model.joblib",
    filepath: Optional[str] = None,
) -> Dict[str, Any]:
    """Evaluate persisted demand model on the test dataset."""
    suite = DemandModelSuite.load_artifacts(filepath=artifact_path)
    return {
        "best_model_name": suite.best_model_name,
        "top_features": dict(list(suite.feature_importance.items())[:10]),
        "per_item_test_metrics_sample": dict(list(suite.per_item_test_metrics.items())[:5]),
    }


def predict_item_demand(
    date: str,
    items: Optional[List[str]] = None,
    is_holiday: int = 0,
    is_promotion: int = 0,
    history_cutoff_date: Optional[str] = None,
    buffer_pct: float = 0.10,
    kitchen_capacity: Optional[int] = 500,
    min_batch_size: int = 0,
    batch_multiple: int = 5,
    artifact_path: str = "ml/artifacts/demand_model.joblib",
    filepath: Optional[str] = None,
) -> Dict[str, Any]:
    """Generate point forecasts and uncertainty intervals for all eligible items on a target date.

    Strict zero-leakage: Any observations after the forecasting origin date are strictly excluded.
    """
    suite = DemandModelSuite.load_artifacts(filepath=artifact_path)
    fe_path = Path(artifact_path).parent / "feature_engineer.joblib"
    if not fe_path.exists():
        raise FileNotFoundError(f"Feature engineer artifact missing at '{fe_path}'. Please train first.")
    fe: CanteenFeatureEngineer = joblib.load(fe_path)

    # Load uncertainty estimator if available
    unc_path = Path(artifact_path).parent / "uncertainty_estimator.joblib"
    unc_est: Optional[DemandUncertaintyEstimator] = joblib.load(unc_path) if unc_path.exists() else None

    loader = CanteenDataLoader(filepath=filepath)
    clean_df, _ = loader.load_and_validate()

    target_dt = pd.to_datetime(date)
    day_name = target_dt.day_name()
    dow = target_dt.day_of_week

    # Strict zero-leakage origin: strictly filter out same-day or future observations
    if history_cutoff_date is not None:
        cutoff_dt = pd.to_datetime(history_cutoff_date)
    else:
        cutoff_dt = target_dt - pd.Timedelta(days=1)

    known_history = clean_df[clean_df["date"] <= cutoff_dt].copy()
    if len(known_history) == 0:
        known_history = clean_df.copy()

    all_items = clean_df["item_name"].unique().tolist()
    if items:
        all_items = [it for it in all_items if it in items]

    item_meta = clean_df.drop_duplicates("item_name").set_index("item_name")
    rows = []
    planner = PreparationPlanner(
        default_buffer_pct=buffer_pct,
        default_kitchen_capacity=kitchen_capacity,
        default_batch_size=batch_multiple,
    )

    for item in all_items:
        meta = item_meta.loc[item]
        hist_mean = fe.item_historical_stats.get(item, 15.0)

        item_history = known_history[known_history["item_name"] == item].sort_values("date")
        if len(item_history) > 0:
            last_sold = float(item_history["qty_sold"].iloc[-1])
            lag_7 = float(item_history["qty_sold"].iloc[-7]) if len(item_history) >= 7 else last_sold
            lag_14 = float(item_history["qty_sold"].iloc[-14]) if len(item_history) >= 14 else lag_7
            r7_mean = float(item_history["qty_sold"].tail(7).mean())
            r7_std = float(item_history["qty_sold"].tail(7).std()) if len(item_history) >= 2 else 2.0
            r14_mean = float(item_history["qty_sold"].tail(14).mean())
            r28_mean = float(item_history["qty_sold"].tail(28).mean())
        else:
            last_sold = float(hist_mean)
            lag_7 = float(hist_mean)
            lag_14 = float(hist_mean)
            r7_mean = float(hist_mean)
            r7_std = 2.0
            r14_mean = float(hist_mean)
            r28_mean = float(hist_mean)

        feat_dict = {
            "price": float(meta["price"]),
            "cost": float(meta["cost"]),
            "margin": round(float(meta["price"]) - float(meta["cost"]), 2),
            "margin_pct": round(((float(meta["price"]) - float(meta["cost"])) / float(meta["price"])) * 100.0, 2),
            "calories": float(meta["calories"]),
            "rating": float(meta["rating"]),
            "day_of_week": dow,
            "is_weekend": int(dow in [5, 6]),
            "month": target_dt.month,
            "day_of_month": target_dt.day,
            "sin_dow": np.sin(2 * np.pi * dow / 7.0),
            "cos_dow": np.cos(2 * np.pi * dow / 7.0),
            "sin_month": np.sin(2 * np.pi * target_dt.month / 12.0),
            "cos_month": np.cos(2 * np.pi * target_dt.month / 12.0),
            "is_holiday": is_holiday,
            "promotion": is_promotion,
            "lag_1d": float(last_sold),
            "lag_2d": float(last_sold),
            "lag_7d": float(lag_7),
            "lag_14d": float(lag_14),
            "rolling_7d_mean": float(r7_mean),
            "rolling_7d_std": float(r7_std) if pd.notna(r7_std) else 0.0,
            "rolling_14d_mean": float(r14_mean),
            "rolling_28d_mean": float(r28_mean),
            "item_historical_mean": float(hist_mean),
        }

        for cat in fe.category_list:
            feat_dict[f"cat_{cat}"] = 1 if meta["category"] == cat else 0

        x_row = pd.DataFrame([feat_dict])[suite.feature_names]
        pred_val = max(0.0, float(suite.best_model.predict(x_row)[0]))

        if unc_est is not None:
            p10_arr, _, p90_arr = unc_est.predict_intervals(x_row, point_predictions=np.array([pred_val]))
            p10 = float(p10_arr[0])
            p90 = float(p90_arr[0])
        else:
            p10 = max(0.0, float(suite.lower_quantile_model.predict(x_row)[0])) if suite.lower_quantile_model else pred_val * 0.85
            p90 = max(pred_val, float(suite.upper_quantile_model.predict(x_row)[0])) if suite.upper_quantile_model else pred_val * 1.20

        prep_calc = planner.calculate_preparation(
            item_name=item,
            predicted_demand=pred_val,
            buffer_pct=buffer_pct,
            kitchen_capacity=kitchen_capacity,
            min_batch_size=min_batch_size,
            batch_multiple=batch_multiple,
        )

        rows.append({
            "item_name": item,
            "category": str(meta["category"]),
            "predicted_demand": round(pred_val, 1),
            "p10_pessimistic_demand": round(p10, 1),
            "p90_surge_demand": round(p90, 1),
            "recommended_preparation": prep_calc["recommended_preparation"],
        })

    total_pred = sum(r["predicted_demand"] for r in rows)
    total_prep = sum(r["recommended_preparation"] for r in rows)

    return {
        "date": date,
        "day_of_week": day_name,
        "total_predicted_demand": round(total_pred, 1),
        "total_recommended_preparation": total_prep,
        "items_count": len(rows),
        "predictions": rows,
    }


def predict_7_day_demand(
    start_date: str,
    items: Optional[List[str]] = None,
    buffer_pct: float = 0.10,
    kitchen_capacity: Optional[int] = 500,
    min_batch_size: int = 0,
    batch_multiple: int = 5,
    artifact_path: str = "ml/artifacts/demand_model.joblib",
    filepath: Optional[str] = None,
) -> Dict[str, Any]:
    """Generate forward 7-day demand forecasts and uncertainty bounds using genuine recursive multi-step forecasting.

    Strict zero-leakage guarantee:
    1. Origin is strictly established as start_date - 1 day (or latest available historical observation).
    2. Any records after origin are strictly filtered out; deleting or altering future sales has zero impact on forecasts.
    3. Multi-step forecasting dynamically feeds previous predictions as lag_1d and rolling statistics for future dates.
    """
    suite = DemandModelSuite.load_artifacts(filepath=artifact_path)
    fe_path = Path(artifact_path).parent / "feature_engineer.joblib"
    if not fe_path.exists():
        raise FileNotFoundError(f"Feature engineer artifact missing at '{fe_path}'. Please train first.")
    fe: CanteenFeatureEngineer = joblib.load(fe_path)

    unc_path = Path(artifact_path).parent / "uncertainty_estimator.joblib"
    unc_est: Optional[DemandUncertaintyEstimator] = joblib.load(unc_path) if unc_path.exists() else None

    loader = CanteenDataLoader(filepath=filepath)
    clean_df, _ = loader.load_and_validate()

    start_dt = pd.to_datetime(start_date)
    origin_dt = start_dt - pd.Timedelta(days=1)
    if clean_df["date"].max() < origin_dt:
        origin_dt = clean_df["date"].max()

    # Known historical data strictly on or before origin_dt (prevents future leakage)
    known_history = clean_df[clean_df["date"] <= origin_dt].copy()
    if len(known_history) == 0:
        known_history = clean_df.copy()

    all_items = clean_df["item_name"].unique().tolist()
    if items:
        all_items = [it for it in all_items if it in items]

    item_meta = clean_df.drop_duplicates("item_name").set_index("item_name")
    planner = PreparationPlanner(
        default_buffer_pct=buffer_pct,
        default_kitchen_capacity=kitchen_capacity,
        default_batch_size=batch_multiple,
    )

    # Initialize rolling tracking buffer per item: list of (pd.Timestamp, float_qty)
    item_buffers: Dict[str, List[Tuple[pd.Timestamp, float]]] = {}
    for item in all_items:
        item_hist = known_history[known_history["item_name"] == item].sort_values("date")
        if len(item_hist) > 0:
            tail_obs = item_hist.tail(35)
            item_buffers[item] = [
                (pd.to_datetime(r["date"]), float(r["qty_sold"]))
                for _, r in tail_obs.iterrows()
            ]
        else:
            fallback = float(fe.item_historical_stats.get(item, 15.0))
            item_buffers[item] = [
                (origin_dt - pd.Timedelta(days=i), fallback) for i in range(35, 0, -1)
            ]

    daily_forecasts = []
    tot_dem = 0.0
    tot_prep = 0

    # Recursive 7-Day Rollout
    for d in range(7):
        target_dt = start_dt + pd.Timedelta(days=d)
        target_date_str = target_dt.strftime("%Y-%m-%d")
        day_name = target_dt.day_name()
        dow = target_dt.day_of_week

        daily_rows = []
        for item in all_items:
            meta = item_meta.loc[item]
            hist_mean = float(fe.item_historical_stats.get(item, 15.0))
            buf = item_buffers[item]

            # Construct dynamic lags from known history + prior recursive predictions
            # lag_1d is the most recent observation (day d-1)
            lag_1 = buf[-1][1] if len(buf) >= 1 else hist_mean
            lag_2 = buf[-2][1] if len(buf) >= 2 else lag_1
            lag_7 = buf[-7][1] if len(buf) >= 7 else lag_1
            lag_14 = buf[-14][1] if len(buf) >= 14 else lag_7

            past_qtys = [q for _, q in buf]
            r7_vals = past_qtys[-7:] if len(past_qtys) >= 7 else past_qtys
            r14_vals = past_qtys[-14:] if len(past_qtys) >= 14 else past_qtys
            r28_vals = past_qtys[-28:] if len(past_qtys) >= 28 else past_qtys

            r7_mean = float(np.mean(r7_vals))
            r7_std = float(np.std(r7_vals)) if len(r7_vals) >= 2 else 2.0
            r14_mean = float(np.mean(r14_vals))
            r28_mean = float(np.mean(r28_vals))

            feat_dict = {
                "price": float(meta["price"]),
                "cost": float(meta["cost"]),
                "margin": round(float(meta["price"]) - float(meta["cost"]), 2),
                "margin_pct": round(((float(meta["price"]) - float(meta["cost"])) / float(meta["price"])) * 100.0, 2),
                "calories": float(meta["calories"]),
                "rating": float(meta["rating"]),
                "day_of_week": dow,
                "is_weekend": int(dow in [5, 6]),
                "month": target_dt.month,
                "day_of_month": target_dt.day,
                "sin_dow": np.sin(2 * np.pi * dow / 7.0),
                "cos_dow": np.cos(2 * np.pi * dow / 7.0),
                "sin_month": np.sin(2 * np.pi * target_dt.month / 12.0),
                "cos_month": np.cos(2 * np.pi * target_dt.month / 12.0),
                "is_holiday": 0,
                "promotion": 0,
                "lag_1d": float(lag_1),
                "lag_2d": float(lag_2),
                "lag_7d": float(lag_7),
                "lag_14d": float(lag_14),
                "rolling_7d_mean": float(r7_mean),
                "rolling_7d_std": float(r7_std) if pd.notna(r7_std) else 0.0,
                "rolling_14d_mean": float(r14_mean),
                "rolling_28d_mean": float(r28_mean),
                "item_historical_mean": float(hist_mean),
            }

            for cat in fe.category_list:
                feat_dict[f"cat_{cat}"] = 1 if meta["category"] == cat else 0

            x_row = pd.DataFrame([feat_dict])[suite.feature_names]
            pred_val = max(0.0, float(suite.best_model.predict(x_row)[0]))

            if unc_est is not None:
                p10_arr, _, p90_arr = unc_est.predict_intervals(x_row, point_predictions=np.array([pred_val]))
                p10 = float(p10_arr[0])
                p90 = float(p90_arr[0])
            else:
                p10 = max(0.0, float(suite.lower_quantile_model.predict(x_row)[0])) if suite.lower_quantile_model else pred_val * 0.85
                p90 = max(pred_val, float(suite.upper_quantile_model.predict(x_row)[0])) if suite.upper_quantile_model else pred_val * 1.20

            prep_calc = planner.calculate_preparation(
                item_name=item,
                predicted_demand=pred_val,
                buffer_pct=buffer_pct,
                kitchen_capacity=kitchen_capacity,
                min_batch_size=min_batch_size,
                batch_multiple=batch_multiple,
            )

            # RECURSIVE UPDATE: Append predicted value to buffer for future horizon steps
            buf.append((target_dt, pred_val))

            spread = p90 - p10
            daily_rows.append({
                "item_name": item,
                "category": str(meta["category"]),
                "predicted_demand": round(pred_val, 1),
                "p10_lower_bound": round(p10, 1),
                "p90_upper_bound": round(p90, 1),
                "recommended_preparation": prep_calc["recommended_preparation"],
                "risk_level": "HIGH_UNCERTAINTY" if spread > 16.0 else "NORMAL",
            })

        day_total_pred = sum(r["predicted_demand"] for r in daily_rows)
        day_total_prep = sum(r["recommended_preparation"] for r in daily_rows)

        tot_dem += day_total_pred
        tot_prep += day_total_prep

        daily_forecasts.append({
            "date": target_date_str,
            "day_of_week": day_name,
            "is_holiday": 0,
            "is_promotion": 0,
            "total_predicted_demand": round(day_total_pred, 1),
            "total_recommended_preparation": day_total_prep,
            "items": daily_rows,
        })

    end_date_str = (start_dt + pd.Timedelta(days=6)).strftime("%Y-%m-%d")
    return {
        "start_date": start_date,
        "end_date": end_date_str,
        "total_forecast_demand": round(tot_dem, 1),
        "total_forecast_preparation": tot_prep,
        "daily_forecasts": daily_forecasts,
    }


def calculate_preparation_quantity(
    predicted_demand: float,
    item_name: str = "Dish",
    buffer_pct: float = 0.10,
    kitchen_capacity: Optional[int] = 500,
    min_batch_size: int = 0,
    batch_multiple: int = 5,
    enable_adaptive_buffer: bool = False,
    historical_waste_rate_pct: Optional[float] = None,
    demand_uncertainty_std: Optional[float] = None,
) -> Dict[str, Any]:
    """Calculate recommended cooking portions with buffers and batching."""
    planner = PreparationPlanner(
        default_buffer_pct=buffer_pct,
        default_kitchen_capacity=kitchen_capacity,
        default_batch_size=batch_multiple,
    )
    return planner.calculate_preparation(
        item_name=item_name,
        predicted_demand=predicted_demand,
        buffer_pct=buffer_pct,
        kitchen_capacity=kitchen_capacity,
        min_batch_size=min_batch_size,
        batch_multiple=batch_multiple,
        enable_adaptive_buffer=enable_adaptive_buffer,
        historical_waste_rate_pct=historical_waste_rate_pct,
        demand_uncertainty_std=demand_uncertainty_std,
    )


def generate_weekly_menu(
    start_date: str = "2025-05-12",
    daily_budget_inr: float = 45000.0,
    daily_capacity_portions: int = 800,
    min_dishes_per_day: int = 8,
    max_dishes_per_day: int = 14,
    required_categories: Optional[List[str]] = None,
    min_avg_calories: float = 250.0,
    max_avg_calories: float = 650.0,
    filepath: Optional[str] = None,
) -> Dict[str, Any]:
    """Generate an optimal 7-day menu mix using MILP."""
    loader = CanteenDataLoader(filepath=filepath)
    clean_df, _ = loader.load_and_validate()

    candidate_items = clean_df.groupby("item_name").agg(
        category=("category", "first"),
        price=("price", "mean"),
        cost=("cost", "mean"),
        calories=("calories", "first"),
        rating=("rating", "mean"),
    ).reset_index()

    forecast_rows = []
    clean_df["dow"] = clean_df["date"].dt.day_of_week
    dow_means = clean_df.groupby(["item_name", "dow"])["qty_sold"].mean().reset_index()
    for _, r in dow_means.iterrows():
        forecast_rows.append({
            "item_name": r["item_name"],
            "day_of_week": int(r["dow"]),
            "predicted_demand": max(1.0, float(r["qty_sold"])),
        })
    weekly_forecast_df = pd.DataFrame(forecast_rows)

    optimizer = MenuMixOptimizer(
        daily_capacity_portions=daily_capacity_portions,
        daily_budget_inr=daily_budget_inr,
        min_dishes_per_day=min_dishes_per_day,
        max_dishes_per_day=max_dishes_per_day,
    )

    return optimizer.optimize_weekly_menu(
        candidate_items_df=candidate_items,
        weekly_forecast_df=weekly_forecast_df,
        start_date=start_date,
        required_categories=required_categories,
        min_avg_calories=min_avg_calories,
        max_avg_calories=max_avg_calories,
    )


def analyze_food_waste(
    filepath: Optional[str] = None,
    waste_disposal_cost: float = 2.0,
) -> Dict[str, Any]:
    """Analyze historical waste and identify chronic high-waste items."""
    loader = CanteenDataLoader(filepath=filepath)
    clean_df, _ = loader.load_and_validate()
    analyzer = WasteAnalyzer(waste_disposal_cost=waste_disposal_cost)
    return analyzer.analyze_operational_waste(clean_df)


def recommend_surplus_discounts(
    surplus_inventory: List[Dict[str, Any]],
    current_time_str: str = "16:30",
    manager_safety_override: bool = False,
    waste_disposal_cost: float = 2.0,
) -> Dict[str, Any]:
    """Recommend discount tiers and construct Mystery Meal rescue boxes with food safety checks."""
    recommender = SurplusFoodRecommender(waste_disposal_cost=waste_disposal_cost)
    return recommender.recommend_discounts(
        surplus_inventory=surplus_inventory,
        current_time_str=current_time_str,
        manager_safety_override=manager_safety_override,
    )


def recommend_procurement(
    weekly_menu_plan: Optional[Dict[str, Any]] = None,
    current_inventory_stock: Optional[Dict[str, float]] = None,
    start_date: str = "2025-05-12",
    filepath: Optional[str] = None,
) -> Dict[str, Any]:
    """Calculate raw ingredient procurement demands and detect pantry shortages/spoilage risks."""
    if weekly_menu_plan is None:
        weekly_menu_plan = generate_weekly_menu(start_date=start_date, filepath=filepath)

    advisor = ProcurementAdvisor()
    return advisor.calculate_ingredient_procurement(
        weekly_menu_plan=weekly_menu_plan,
        current_inventory_stock=current_inventory_stock,
    )


def calculate_regret_metrics(
    filepath: Optional[str] = None,
    waste_disposal_cost: float = 2.0,
) -> Dict[str, Any]:
    """Calculate the Regret Meter: avoidable financial loss and normalized 0-100 regret score."""
    loader = CanteenDataLoader(filepath=filepath)
    clean_df, _ = loader.load_and_validate()
    analyzer = WasteAnalyzer(waste_disposal_cost=waste_disposal_cost)
    return analyzer.calculate_regret_meter(clean_df)
