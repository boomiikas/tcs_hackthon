"""Pydantic data schemas and contracts for CanteenIQ ML & FastAPI integration."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


# -------------------------------------------------------------
# Module 2: Demand Prediction Schemas
# -------------------------------------------------------------
class DemandPredictionRequest(BaseModel):
    date: str = Field(..., description="Target service date in YYYY-MM-DD format", json_schema_extra={"example": "2025-05-12"})
    items: Optional[List[str]] = Field(None, description="Optional subset of item names to forecast")
    is_holiday: Optional[int] = Field(0, description="1 if campus holiday/break, 0 otherwise")
    is_promotion: Optional[int] = Field(0, description="1 if promotional campaign active, 0 otherwise")


class ItemDemandPrediction(BaseModel):
    item_name: str
    category: str
    predicted_demand: float
    p10_pessimistic_demand: float
    p90_surge_demand: float
    recommended_preparation: int


class DemandPredictionResponse(BaseModel):
    date: str
    day_of_week: str
    total_predicted_demand: float
    total_recommended_preparation: int
    items_count: int
    predictions: List[ItemDemandPrediction]


# -------------------------------------------------------------
# Module 3: Preparation Planning Schemas
# -------------------------------------------------------------
class StagedPreparationPlan(BaseModel):
    staged_cooking_enabled: bool
    batch_1_morning: int
    batch_2_midday: int
    batch_2_trigger_rule: str


class PreparationCalculationRequest(BaseModel):
    item_name: str
    predicted_demand: float
    buffer_pct: Optional[float] = Field(0.10, description="Safety buffer rate (e.g. 0.10 for +10%)")
    kitchen_capacity: Optional[int] = Field(500, description="Maximum portion ceiling")
    min_batch_size: Optional[int] = Field(0, description="Minimum batch quantity")
    batch_multiple: Optional[int] = Field(5, description="Cooking batch multiple (e.g. 5)")
    enable_adaptive_buffer: Optional[bool] = False
    historical_waste_rate_pct: Optional[float] = None
    demand_uncertainty_std: Optional[float] = None


class PreparationCalculationResponse(BaseModel):
    item_name: str
    predicted_demand: float
    buffer_percentage: float
    buffer_portions: int
    recommended_preparation: int
    estimated_surplus: int
    kitchen_capacity: Optional[int]
    min_batch_size: int
    batch_multiple: int
    has_capacity_conflict: bool
    conflict_message: Optional[str]
    staged_preparation: StagedPreparationPlan


# -------------------------------------------------------------
# Module 4: Menu Mix Optimization Schemas
# -------------------------------------------------------------
class MenuOptimizationRequest(BaseModel):
    start_date: str = Field("2025-05-12", description="Monday start date in YYYY-MM-DD format")
    daily_budget_inr: Optional[float] = Field(45000.0, description="Maximum daily preparation budget")
    daily_capacity_portions: Optional[int] = Field(800, description="Maximum total daily cooked portions")
    min_dishes_per_day: Optional[int] = Field(8, description="Minimum dishes offered per day")
    max_dishes_per_day: Optional[int] = Field(14, description="Maximum dishes offered per day")
    required_categories: Optional[List[str]] = Field(
        default=["Beverages", "Rice Bowl", "Sandwich"],
        description="Categories that must have at least 1 dish daily"
    )
    min_avg_calories: Optional[float] = 250.0
    max_avg_calories: Optional[float] = 650.0


class MenuItemPlan(BaseModel):
    item_name: str
    category: str
    price: float
    cost: float
    calories: int
    rating: float
    predicted_demand: int
    recommended_preparation: int
    expected_sold: int
    expected_waste: int
    expected_revenue: float
    expected_cost: float
    expected_waste_cost: float
    expected_profit: float


class DailyMenuPlan(BaseModel):
    date: str
    day_of_week: str
    dishes_count: int
    total_portions_prepared: int
    total_expected_revenue: float
    total_expected_profit: float
    avg_calories_per_dish: float
    menu_items: List[MenuItemPlan]


class MenuOptimizationResponse(BaseModel):
    start_date: str
    days_planned: int
    daily_plans: List[DailyMenuPlan]
    baseline_comparison: Dict[str, Any]
    selection_rationale: str


# -------------------------------------------------------------
# Module 5: Waste Analysis & Mystery Meal Schemas
# -------------------------------------------------------------
class SurplusItemInput(BaseModel):
    item_name: str
    category: str
    price: float
    surplus_portions: int


class MysteryMealRequest(BaseModel):
    surplus_items: List[SurplusItemInput]
    discount_pct: Optional[float] = Field(35.0, description="Discount off regular combined price")


class FoodSafetyNotice(BaseModel):
    requires_manual_inspection: bool
    holding_time_limit_hours: float
    temperature_specification: str
    safety_guideline: str


class MysteryMealResponse(BaseModel):
    combo_available: bool
    combo_name: Optional[str] = None
    bundled_items: Optional[List[str]] = None
    max_combos_available: Optional[int] = None
    original_total_price_inr: Optional[float] = None
    discount_percentage: Optional[float] = None
    rescue_combo_price_inr: Optional[float] = None
    estimated_portions_saved: Optional[int] = None
    food_safety_notice: Optional[FoodSafetyNotice] = None
    message: Optional[str] = None


# -------------------------------------------------------------
# Module 2 & 5: Regret Meter & 7-Day Forecast Schemas
# -------------------------------------------------------------
class SevenDayForecastRequest(BaseModel):
    start_date: str = Field(..., description="Start date in YYYY-MM-DD format", json_schema_extra={"example": "2025-05-12"})
    items: Optional[List[str]] = Field(None, description="Optional list of items to forecast")


class DailyDishForecast(BaseModel):
    item_name: str
    category: str
    predicted_demand: float
    p10_lower_bound: float
    p90_upper_bound: float
    recommended_preparation: int
    risk_level: str


class SingleDayForecast(BaseModel):
    date: str
    day_of_week: str
    is_holiday: int
    is_promotion: int
    total_predicted_demand: float
    total_recommended_preparation: int
    items: List[DailyDishForecast]


class SevenDayForecastResponse(BaseModel):
    start_date: str
    end_date: str
    total_forecast_demand: float
    total_forecast_preparation: int
    daily_forecasts: List[SingleDayForecast]


class RegretMeterResponse(BaseModel):
    regret_index_score: float
    operational_efficiency_score: float
    status: str
    currency: Optional[str] = "INR"
    time_period_audited: Optional[Dict[str, Any]] = None
    total_avoidable_financial_loss_inr: float
    waste_regret_loss_inr: float
    stockout_missed_margin_loss_inr: float
    total_realized_revenue_inr: float
    total_wasted_portions: int
    total_missed_demand_portions: int
    daily_averages: Optional[Dict[str, Any]] = None
    weekly_averages: Optional[Dict[str, Any]] = None
    manager_assessment: str
    methodology_note: Optional[str] = None
    formula_documentation: Optional[Dict[str, Any]] = None


# -------------------------------------------------------------
# Module 6 & 7: Surplus Discounts & Procurement Schemas
# -------------------------------------------------------------
class SurplusDiscountItem(BaseModel):
    item_name: str
    category: str
    original_price_inr: float
    discount_percentage: float
    discounted_price_inr: float
    surplus_portions: int
    potential_recovery_revenue_inr: float
    food_safety: Dict[str, Any]


class SurplusDiscountResponse(BaseModel):
    current_time: str
    applied_discount_tier: str
    discount_percentage: float
    eligible_surplus_items_count: int
    unsafe_disqualified_items_count: int
    total_potential_recovery_revenue_inr: float
    total_disposal_costs_avoided_inr: float
    total_financial_value_salvaged_inr: float
    discounted_items: List[SurplusDiscountItem]
    unsafe_items_flagged: List[Dict[str, Any]]
    mystery_meal_bundle: Dict[str, Any]


class ProcurementOrder(BaseModel):
    ingredient_name: str
    unit: str
    menu_required_quantity: float
    current_pantry_stock: float
    recommended_order_quantity: float
    is_perishable: bool


class ProcurementResponse(BaseModel):
    total_weekly_portions_planned: int
    distinct_ingredients_required: int
    critical_shortages_count: int
    spoilage_risks_count: int
    is_simulated_inventory: bool
    procurement_order_list: List[ProcurementOrder]
    projected_shortages: List[Dict[str, Any]]
    projected_overstock_risks: List[Dict[str, Any]]
    data_lineage_notes: str

