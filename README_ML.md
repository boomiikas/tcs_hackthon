# CanteenIQ — Machine Learning & Optimization Engine
## AI-Powered Canteen Menu Mix Optimization & Food Waste Reduction (PS 2.1)

---

### Executive Overview

**CanteenIQ** provides cafeteria managers, food service providers, and campus operators with an end-to-end mathematical optimization and demand forecasting engine. It solves the core problem of static canteen menus:
- Disproportionate ingredient costs and surplus food waste caused by static, un-optimized menus.
- Mismatch between kitchen preparation quantities and actual student demand.
- Inability to dynamically adjust menus to student ratings, dietary targets, and seasonal campus trends.

This package contains the complete, production-ready machine learning and optimization core designed for seamless integration with your team's **FastAPI** backend and **MongoDB Atlas** persistence layer.

---

## 1. Module Architecture & Folder Structure

```
ml/
├── __init__.py               # Unified public Python API (load, train, evaluate, predict, optimize)
├── data_loader.py            # Dataset discovery, schema normalization, and numerical validation
├── preprocessing.py          # Leakage-free feature engineering & chronological splitting
├── eda.py                    # Exploratory data analysis, waste audits, and KPI reports
├── demand_model.py           # Baseline vs Random Forest vs HistGradientBoosting & Quantiles
├── preparation_planner.py    # Buffer planning, cooking batches, capacity bounds, and staged prep
├── menu_optimizer.py         # SciPy HiGHS Mixed-Integer Linear Programming (MILP) menu solver
├── waste_analyzer.py         # Chronic waste detection, prep adjustments, and Mystery Meal builder
├── schemas.py                # Pydantic request/response data contracts for FastAPI
├── train.py                  # CLI reproducible training and model evaluation pipeline
├── predict.py                # CLI inference, prep planning, and menu optimization demo
├── artifacts/                # Persisted joblib models & feature transformers
│   ├── demand_model.joblib
│   └── feature_engineer.joblib
└── reports/                  # Generated audit reports and evaluation benchmarks
    ├── eda_report.md
    ├── eda_summary.json
    ├── model_evaluation_report.md
    └── model_metrics.json
```

---

## 2. Key Capabilities by Module

### Module 1: Preprocessing & Leakage Prevention (`data_loader.py`, `preprocessing.py`, `eda.py`)
- **Strict Data Leakage Prevention**: Same-day actual sales (`qty_sold`), preparation (`qty_prepared`), and waste (`qty_wasted`) are strictly excluded from feature inputs.
- **Temporal Lag & Rolling Features**: Lags (`lag_1d`, `lag_2d`, `lag_7d`, `lag_14d`) and moving windows (`rolling_7d_mean`, `rolling_14d_mean`, `rolling_28d_mean`) are grouped per item and shifted by at least 1 day ($t-1$).
- **Calendar & Cyclical Dynamics**: Cyclical sine/cosine transforms for day of week and month, plus academic holiday and promotional flags.
- **Chronological Splitting**: Train (70%), Validation (15%), and Test (15%) splits partitioned strictly along the calendar timeline.

### Module 2: Item-Level Demand Prediction (`demand_model.py`)
- **Model Suite**: Evaluates a 7-day Seasonal Naive Baseline against `RandomForestRegressor` and `HistGradientBoostingRegressor`.
- **Selected Best Model**: `HistGradientBoostingRegressor` (lowest WAPE: **29.1%** validation, **30.7%** unseen test set).
- **Uncertainty Bounds**: Quantile regression models ($p_{10}$ pessimistic demand, $p_{90}$ surge demand) provide confidence intervals for risk-averse kitchen planning.
- **Safe WAPE Calculation**: Zero-division safeguard handles days/items with zero customer demand.

### Module 3: Buffer-Based Preparation Planning (`preparation_planner.py`)
- **Core Formula**:
  $$\text{Recommended Preparation} = \min(\text{Kitchen Capacity}, \lceil \text{Predicted Demand} \times (1 + \text{Buffer Rate}) \rceil)$$
- **Batching & Constraints**: Rounds quantities to cooking batch increments (e.g., trays of 5 portions).
- **Conflict Handling**: Explicitly flags structural conflicts if minimum batch quantity exceeds kitchen capacity.
- **Staged Cooking Workflow**:
  - **Batch 1 (Morning)**: Cook 70% of recommended portions.
  - **Batch 2 (Midday Review)**: Cook remaining 30% only if morning sales exceed 60% of forecast by 12:30 PM.

### Module 4: Weekly Menu Mix Optimization (`menu_optimizer.py`)
- **Mathematical Solver**: Mixed-Integer Linear Programming (MILP) solved using SciPy's modern HiGHS solver.
- **Objective**: Maximize net contribution (Revenue minus Prep Cost minus Waste Cost) plus student satisfaction bonus ($\text{Rating} \ge 4.5$), while minimizing expected surplus waste.
- **Constraints**:
  1. **Menu Variety**: 8 to 14 dishes featured daily.
  2. **Category Coverage**: At least 1 dish per core category (Beverages, Rice Bowls, Sandwiches, etc.) daily.
  3. **Kitchen Capacity**: Total cooked portions $\le 800$ portions/day.
  4. **Daily Ingredient Budget**: Total preparation cost $\le \text{INR } 45,000$/day.
  5. **Nutrition Target**: Average dish calories balanced between 250 and 650 kcal.
  6. **Anti-Fatigue**: Specialty dishes limited to max 4 days/week; core staples allowed daily.
- **Impact vs Static Baseline**:
  - **Net Profit Uplift**: **+20.5%**
  - **Food Waste Reduction**: **-65.3%** (**403 portions saved per week!**)

### Module 5: Waste & Surplus Analysis (`waste_analyzer.py`)
- **Chronic High-Waste Detection**: Flags dishes with $>25\%$ waste rate or high accumulated disposal costs.
- **Actionable Prep Adjustments**: Recommends "REDUCE PREPARATION by 15-20%" for over-prepared dishes or "INCREASE PREPARATION" for dishes with stockouts ($>20\%$).
- **Mystery Meal Surplus Rescue**:
  - Automatically bundles eligible surplus mains, beverages, and snacks into a discounted combo (e.g. 35% discount).
  - **Food Safety Guard**: Enforces hot holding limits ($\le 4$ hours, $\ge 60^\circ\text{C}$). If temperature logs are missing, flags `requires_manual_inspection: true`.

---

## 3. Measured Model Performance & Benchmarks

Measured on the 52-week operational dataset:

| Model Candidate | Validation MAE | Validation RMSE | Validation WAPE | Validation R² | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Seasonal Naive Baseline (Lag-7)** | 7.39 portions | 15.99 portions | 65.0% | 0.161 | Benchmark |
| **Random Forest Regressor** | 3.41 portions | 7.38 portions | 30.0% | 0.821 | Candidate |
| **HistGradientBoosting Regressor** | **3.31 portions** | **7.99 portions** | **29.1%** | **0.791** | **SELECTED BEST** |

### Unseen Test Set Performance (Weeks 45 to 52):
- **MAE**: **3.17 portions**
- **RMSE**: **7.08 portions**
- **WAPE**: **30.7%**
- **R² Score**: **0.800**

---

## 4. Setup and Quickstart

### 1. Install Dependencies
```powershell
pip install -r requirements-ml.txt
```

### 2. Run Reproducible Training & Evaluation
```powershell
python ml/train.py
```
*Outputs evaluation reports to `ml/reports/` and persisted models to `ml/artifacts/`.*

### 3. Run Inference & Menu Optimization CLI
```powershell
# 1. Forecast demand for a specific date
python -m ml.predict predict --date 2025-12-15

# 2. Generate 7-day multi-horizon forecast
python -m ml.predict predict-7days --start-date 2025-12-15

# 3. Calculate preparation with buffer & staged batches
python -m ml.predict plan-prep --item "Paneer Butter Masala Rice Bowl" --demand 75 --buffer 0.10

# 4. Generate 7-day optimized menu plan
python -m ml.predict optimize-menu --start-date 2025-12-15

# 5. Run historical waste audit
python -m ml.predict audit-waste

# 6. Audit Avoidable Financial Loss (Regret Meter)
python -m ml.predict regret-meter

# 7. Surplus Food Rescue & Tiered Discounts
python -m ml.predict surplus --time 17:00

# 8. Weekly Raw Ingredient Procurement Explosion
python -m ml.predict procurement --start-date 2025-12-15
```

### 4. Run Unit Tests
```powershell
python -m pytest tests/
```

---

## 5. FastAPI Backend Integration Guide

Your teammates building the FastAPI backend can import and call `ml` functions directly. All input and output payloads conform to Pydantic models in `ml/schemas.py`.

### Example 1: Demand Prediction (`POST /api/v1/predict-demand`)

```python
from fastapi import APIRouter
from ml import predict_item_demand
from ml.schemas import DemandPredictionRequest, DemandPredictionResponse

router = APIRouter()

@router.post("/predict-demand", response_model=DemandPredictionResponse)
def get_demand_forecast(req: DemandPredictionRequest):
    result = predict_item_demand(
        date=req.date,
        items=req.items,
        is_holiday=req.is_holiday,
        is_promotion=req.is_promotion,
    )
    return result
```

#### Request JSON:
```json
{
  "date": "2025-12-15",
  "is_holiday": 0,
  "is_promotion": 0
}
```

#### Response JSON:
```json
{
  "date": "2025-12-15",
  "day_of_week": "Monday",
  "total_predicted_demand": 252.7,
  "total_recommended_preparation": 400,
  "items_count": 48,
  "predictions": [
    {
      "item_name": "Paneer Butter Masala Rice Bowl",
      "category": "Rice Bowl",
      "predicted_demand": 28.4,
      "p10_pessimistic_demand": 18.2,
      "p90_surge_demand": 38.6,
      "recommended_preparation": 35
    },
    {
      "item_name": "Classic Cold Hazelnut Mocha",
      "category": "Beverages",
      "predicted_demand": 11.8,
      "p10_pessimistic_demand": 7.9,
      "p90_surge_demand": 17.2,
      "recommended_preparation": 15
    }
  ]
}
```

---

### Example 2: Preparation Calculation (`POST /api/v1/plan-preparation`)

```python
from ml import calculate_preparation_quantity
from ml.schemas import PreparationCalculationRequest, PreparationCalculationResponse

@router.post("/plan-preparation", response_model=PreparationCalculationResponse)
def plan_preparation(req: PreparationCalculationRequest):
    return calculate_preparation_quantity(
        item_name=req.item_name,
        predicted_demand=req.predicted_demand,
        buffer_pct=req.buffer_pct,
        kitchen_capacity=req.kitchen_capacity,
        min_batch_size=req.min_batch_size,
        batch_multiple=req.batch_multiple,
        enable_adaptive_buffer=req.enable_adaptive_buffer,
    )
```

#### Request JSON:
```json
{
  "item_name": "Paneer Butter Masala Rice Bowl",
  "predicted_demand": 75.0,
  "buffer_pct": 0.10,
  "kitchen_capacity": 200,
  "batch_multiple": 5
}
```

#### Response JSON:
```json
{
  "item_name": "Paneer Butter Masala Rice Bowl",
  "predicted_demand": 75.0,
  "buffer_percentage": 10.0,
  "buffer_portions": 10,
  "recommended_preparation": 85,
  "estimated_surplus": 10,
  "kitchen_capacity": 200,
  "min_batch_size": 0,
  "batch_multiple": 5,
  "has_capacity_conflict": false,
  "conflict_message": null,
  "staged_preparation": {
    "staged_cooking_enabled": true,
    "batch_1_morning": 60,
    "batch_2_midday": 25,
    "batch_2_trigger_rule": "Cook Batch 2 (25 portions) only if 12:30 PM demand exceeds 45 orders."
  }
}
```

---

### Example 3: Weekly Menu Optimization (`POST /api/v1/optimize-weekly-menu`)

```python
from ml import generate_weekly_menu
from ml.schemas import MenuOptimizationRequest, MenuOptimizationResponse

@router.post("/optimize-weekly-menu", response_model=MenuOptimizationResponse)
def optimize_menu(req: MenuOptimizationRequest):
    return generate_weekly_menu(
        start_date=req.start_date,
        daily_budget_inr=req.daily_budget_inr,
        daily_capacity_portions=req.daily_capacity_portions,
        min_dishes_per_day=req.min_dishes_per_day,
        max_dishes_per_day=req.max_dishes_per_day,
        required_categories=req.required_categories,
        min_avg_calories=req.min_avg_calories,
        max_avg_calories=req.max_avg_calories,
    )
```

#### Response JSON:
```json
{
  "start_date": "2025-12-15",
  "days_planned": 7,
  "baseline_comparison": {
    "ai_optimized_plan": {
      "total_portions_prepared": 1410,
      "total_portions_sold": 1195,
      "total_portions_wasted": 215,
      "waste_rate_percentage": 15.25,
      "expected_gross_revenue": 520450.0,
      "expected_ingredient_cost": 247669.35,
      "expected_net_profit": 272780.65
    },
    "unoptimized_static_baseline": {
      "total_portions_prepared": 1800,
      "total_portions_sold": 1182,
      "total_portions_wasted": 618,
      "waste_rate_percentage": 34.33,
      "expected_net_profit": 226446.56
    },
    "impact_improvements": {
      "profit_increase_pct": "+20.5%",
      "food_waste_reduction_pct": "-65.3%",
      "portions_saved_from_landfill": 403,
      "waste_cost_dollars_saved": 38374.29
    }
  },
  "selection_rationale": "The AI-optimized 7-day menu mix selected an average of 14.0 dishes per day..."
}
```

---

### Example 4: Mystery Meal Surplus Rescue (`POST /api/v1/mystery-meal`)

```python
from ml.waste_analyzer import WasteAnalyzer
from ml.schemas import MysteryMealRequest, MysteryMealResponse

@router.post("/mystery-meal", response_model=MysteryMealResponse)
def rescue_mystery_meal(req: MysteryMealRequest):
    analyzer = WasteAnalyzer()
    inv_dicts = [item.model_dump() for item in req.surplus_items]
    return analyzer.build_mystery_meal_recommendation(
        surplus_inventory=inv_dicts,
        target_discount_pct=req.discount_pct,
    )
```

#### Response JSON:
```json
{
  "combo_available": true,
  "combo_name": "CanteenIQ Eco-Rescue Mystery Box",
  "bundled_items": [
    "Paneer Butter Masala Rice Bowl",
    "Thai Lemongrass Iced Tea",
    "Crispy Spring Rolls with Sweet Chili"
  ],
  "max_combos_available": 8,
  "original_total_price_inr": 485.0,
  "discount_percentage": 35.0,
  "rescue_combo_price_inr": 315.0,
  "estimated_portions_saved": 24,
  "food_safety_notice": {
    "requires_manual_inspection": true,
    "holding_time_limit_hours": 4.0,
    "temperature_specification": "Hot holding verified >= 60°C or chilled <= 5°C",
    "safety_guideline": "CRITICAL: Food safety takes absolute precedence. Inspect aroma, texture, and hot-holding temperature logs before packing rescue meals."
  }
}
```

---

### Example 5: 7-Day Forward Demand Horizon (`POST /api/v1/forecast-7days`)

```python
from ml import predict_7_day_demand
from ml.schemas import ForecastHorizonRequest, ForecastHorizonResponse

@router.post("/forecast-7days", response_model=ForecastHorizonResponse)
def get_7day_forecast(req: ForecastHorizonRequest):
    return predict_7_day_demand(start_date=req.start_date)
```

#### Request JSON:
```json
{
  "start_date": "2025-12-15"
}
```

#### Response JSON:
```json
{
  "start_date": "2025-12-15",
  "end_date": "2025-12-21",
  "total_forecast_demand": 1482.4,
  "total_forecast_preparation": 2560,
  "daily_forecasts": [
    {
      "date": "2025-12-15",
      "day_of_week": "Monday",
      "total_predicted_demand": 252.6,
      "total_recommended_preparation": 400,
      "items_count": 48
    }
  ]
}
```

---

### Example 6: Regret Meter & Avoidable Financial Loss (`GET /api/v1/regret-meter`)

```python
from ml import calculate_regret_metrics
from ml.schemas import RegretMetricsResponse

@router.get("/regret-meter", response_model=RegretMetricsResponse)
def get_regret_meter():
    return calculate_regret_metrics()
```

#### Response JSON:
```json
{
  "regret_index_score": 29.1,
  "operational_efficiency_score": 70.9,
  "status": "MODERATE_REGRET",
  "currency": "INR",
  "time_period_audited": {
    "total_operating_days": 364,
    "total_weeks": 52.0,
    "start_date": "2025-01-06",
    "end_date": "2026-01-04",
    "description": "Cumulative 364-day operational audit (52.0 weeks)"
  },
  "total_avoidable_financial_loss_inr": 20060636.38,
  "waste_regret_loss_inr": 14514982.86,
  "stockout_missed_margin_loss_inr": 5545653.52,
  "total_realized_revenue_inr": 48891460.09,
  "total_wasted_portions": 107583,
  "total_missed_demand_portions": 38605,
  "daily_averages": {
    "daily_avoidable_loss_inr": 55111.64,
    "daily_waste_regret_inr": 39876.33,
    "daily_stockout_regret_inr": 15235.31,
    "daily_realized_revenue_inr": 134317.20,
    "daily_wasted_portions": 295.6,
    "daily_missed_demand_portions": 106.1
  },
  "weekly_averages": {
    "weekly_avoidable_loss_inr": 385781.48,
    "weekly_waste_regret_inr": 279134.31,
    "weekly_stockout_regret_inr": 106647.17,
    "weekly_realized_revenue_inr": 940220.40
  },
  "manager_assessment": "Standard institutional variance. Noticeable food waste or missed sales that AI buffering can reclaim."
}
```

---

### Example 7: Dynamic Tiered Surplus Discounts (`POST /api/v1/surplus-discounts`)

```python
from ml import recommend_surplus_discounts
from ml.schemas import SurplusDiscountRequest, SurplusDiscountResponse

@router.post("/surplus-discounts", response_model=SurplusDiscountResponse)
def get_surplus_discounts(req: SurplusDiscountRequest):
    return recommend_surplus_discounts(
        surplus_inventory=[it.model_dump() for it in req.surplus_items],
        current_time_str=req.current_time_str,
        manager_safety_override=req.manager_safety_override,
    )
```

#### Request JSON:
```json
{
  "current_time_str": "17:00",
  "surplus_items": [
    {
      "item_name": "Paneer Butter Masala Rice Bowl",
      "category": "Rice Bowl",
      "price": 268.53,
      "cost": 128.89,
      "surplus_portions": 12,
      "holding_time_hours": 2.5
    },
    {
      "item_name": "Classic Cold Hazelnut Mocha",
      "category": "Beverages",
      "price": 207.94,
      "cost": 91.49,
      "surplus_portions": 18,
      "holding_time_hours": 1.0
    }
  ]
}
```

#### Response JSON:
```json
{
  "evaluation_time": "17:00",
  "applied_discount_tier": "Sunset Canteen Rescue Deal",
  "discount_percentage": 35.0,
  "eligible_surplus_items_count": 2,
  "unsafe_disqualified_items_count": 0,
  "total_potential_recovery_revenue_inr": 4485.0,
  "total_disposal_costs_avoided_inr": 60.0,
  "total_financial_value_salvaged_inr": 4545.0,
  "discounted_items": [
    {
      "item_name": "Paneer Butter Masala Rice Bowl",
      "category": "Rice Bowl",
      "original_price_inr": 268.53,
      "discounted_price_inr": 175.0,
      "surplus_portions": 12,
      "potential_revenue_inr": 2100.0
    }
  ],
  "mystery_meal_bundle": {
    "available": true,
    "bundle_title": "CanteenIQ Eco-Rescue Mystery Box",
    "rescue_combo_price_inr": 310.0,
    "mystery_discount_pct": 45.0,
    "max_combos_packable": 12
  }
}
```

---

### Example 8: Weekly Raw Ingredient Procurement Explosion (`POST /api/v1/procurement`)

```python
from ml import recommend_procurement
from ml.schemas import ProcurementRequest, ProcurementResponse

@router.post("/procurement", response_model=ProcurementResponse)
def plan_procurement(req: ProcurementRequest):
    return recommend_procurement(
        start_date=req.start_date,
        pantry_stock=req.pantry_stock,
    )
```

#### Request JSON:
```json
{
  "start_date": "2025-12-15"
}
```

#### Response JSON:
```json
{
  "start_date": "2025-12-15",
  "total_weekly_portions_planned": 2447,
  "distinct_ingredients_required": 15,
  "critical_shortages_count": 14,
  "spoilage_risks_count": 0,
  "projected_shortages": [
    {
      "ingredient": "Basmati Rice & Grains",
      "unit": "kg",
      "current_stock": 25.0,
      "required_for_menu": 55.4,
      "deficit_to_order": 30.4,
      "urgency": "HIGH_STOCKOUT_RISK"
    }
  ]
}
```
```
