from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime

from database import get_db, init_db
from models import (
    Canteen, FoodItem, Ingredient, RecipeItem,
    DailyOperation, ForecastRecord, WeeklyMenu,
    MenuScheduleItem, SurplusListing, SurplusReservation,
    ProcurementRecommendation
)
from forecasting_service import ForecastingEngine
from optimization_service import MenuOptimizer
from surplus_service import SurplusRecoveryEngine
from procurement_service import ProcurementEngine
from reporting_service import ReportingEngine
from seed_data import seed_data

# Ensure tables and seed exist
init_db()
seed_data()

app = FastAPI(
    title="CanteenIQ Enterprise AI Platform API",
    version="1.0.0",
    description="Intelligent AI Planning, Demand Forecasting, Menu Optimization, Surplus Recovery, and Food-Waste Reduction Platform"
)

# Enable CORS for local Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- CANTEENS & CATALOG ---

@app.get("/api/canteens")
def get_canteens(db: Session = Depends(get_db)):
    canteens = db.query(Canteen).all()
    return [{"id": c.id, "name": c.name, "location": c.location, "daily_capacity": c.daily_capacity, "manager_name": c.manager_name} for c in canteens]

@app.get("/api/food-items")
def get_food_items(meal_period: Optional[str] = None, category: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(FoodItem)
    if meal_period and meal_period != "All":
        q = q.filter(FoodItem.meal_period == meal_period)
    if category and category != "All":
        q = q.filter(FoodItem.category == category)
    items = q.all()
    return [{
        "id": it.id,
        "name": it.name,
        "category": it.category,
        "meal_period": it.meal_period,
        "base_price": it.base_price,
        "prep_cost": it.prep_cost,
        "calories": it.calories,
        "protein_g": it.protein_g,
        "carbs_g": it.carbs_g,
        "fat_g": it.fat_g,
        "allergens": it.allergens,
        "shelf_life_hours": it.shelf_life_hours,
        "standard_batch_size": it.standard_batch_size,
        "image_url": it.image_url,
        "dietary_type": it.dietary_type
    } for it in items]

# --- 1. DASHBOARD ---

@app.get("/api/dashboard")
def get_dashboard_summary(canteen_id: str = "canteen-1", date: str = "2026-10-29", db: Session = Depends(get_db)):
    records = db.query(DailyOperation).filter(
        DailyOperation.canteen_id == canteen_id,
        DailyOperation.date == date
    ).all()

    # KPI Calculations
    total_prepared = sum(r.portions_prepared for r in records)
    total_sold = sum(r.portions_sold for r in records)
    total_discounted = sum(r.portions_discounted for r in records)
    total_discarded = sum(r.portions_discarded for r in records)
    today_revenue = sum(r.revenue for r in records)
    today_cost = sum(r.cost for r in records)
    today_profit = round(today_revenue - today_cost, 2)
    waste_percentage = round((total_discarded / total_prepared) * 100, 1) if total_prepared > 0 else 0.0

    # Hourly / Period Performance
    # Meal period distribution
    period_stats: Dict[str, Dict[str, Any]] = {}
    for r in records:
        if r.meal_period not in period_stats:
            period_stats[r.meal_period] = {"meal_period": r.meal_period, "revenue": 0.0, "portions_sold": 0, "portions_prepared": 0, "discarded": 0}
        p = period_stats[r.meal_period]
        p["revenue"] += r.revenue
        p["portions_sold"] += r.portions_sold
        p["portions_prepared"] += r.portions_prepared
        p["discarded"] += r.portions_discarded

    # Realistic hourly distribution based on actual meal period sales
    hourly_performance = [
        {"time": "08:00 AM", "revenue": round(period_stats.get("Breakfast", {}).get("revenue", 3500) * 0.35, 1), "portions_sold": int(period_stats.get("Breakfast", {}).get("portions_sold", 60) * 0.35)},
        {"time": "09:30 AM", "revenue": round(period_stats.get("Breakfast", {}).get("revenue", 3500) * 0.65, 1), "portions_sold": int(period_stats.get("Breakfast", {}).get("portions_sold", 60) * 0.65)},
        {"time": "11:30 AM", "revenue": round(period_stats.get("Lunch", {}).get("revenue", 12000) * 0.20, 1), "portions_sold": int(period_stats.get("Lunch", {}).get("portions_sold", 110) * 0.20)},
        {"time": "01:00 PM", "revenue": round(period_stats.get("Lunch", {}).get("revenue", 12000) * 0.55, 1), "portions_sold": int(period_stats.get("Lunch", {}).get("portions_sold", 110) * 0.55)},
        {"time": "02:30 PM", "revenue": round(period_stats.get("Lunch", {}).get("revenue", 12000) * 0.25, 1), "portions_sold": int(period_stats.get("Lunch", {}).get("portions_sold", 110) * 0.25)},
        {"time": "04:30 PM", "revenue": round(period_stats.get("Snacks", {}).get("revenue", 4200) * 0.60, 1), "portions_sold": int(period_stats.get("Snacks", {}).get("portions_sold", 70) * 0.60)},
        {"time": "06:00 PM", "revenue": round(period_stats.get("Snacks", {}).get("revenue", 4200) * 0.40, 1), "portions_sold": int(period_stats.get("Snacks", {}).get("portions_sold", 70) * 0.40)},
        {"time": "07:30 PM", "revenue": round(period_stats.get("Dinner", {}).get("revenue", 11000) * 0.60, 1), "portions_sold": int(period_stats.get("Dinner", {}).get("portions_sold", 90) * 0.60)},
        {"time": "09:00 PM", "revenue": round(period_stats.get("Dinner", {}).get("revenue", 11000) * 0.40, 1), "portions_sold": int(period_stats.get("Dinner", {}).get("portions_sold", 90) * 0.40)},
    ]

    # Non-double-counted Preparation and Waste Breakdown
    breakdown = [
        {"name": "Sold Full Price", "portions": total_sold, "color": "#166534", "share_pct": round((total_sold / max(1, total_prepared)) * 100, 1)},
        {"name": "Surplus Recovered", "portions": total_discounted, "color": "#0284c7", "share_pct": round((total_discounted / max(1, total_prepared)) * 100, 1)},
        {"name": "Discarded / Waste", "portions": total_discarded, "color": "#dc2626", "share_pct": round((total_discarded / max(1, total_prepared)) * 100, 1)},
    ]

    # Prioritized AI Recommendations
    recommendations = [
        {
            "id": "REC-01",
            "priority": "High",
            "type": "Production Adjustment",
            "title": "Reduce Friday Poha & Dosa batch size by 15%",
            "reason": "Breakfast historical records over past 3 Fridays show recurring 12-14 portions leftover due to later morning student attendance.",
            "impact": "Saves ₹840 in avoidable prep cost and cuts morning waste to < 2.5%",
            "action_label": "Apply to Forecast",
            "action_route": "/forecasting"
        },
        {
            "id": "REC-02",
            "priority": "Urgent",
            "type": "Surplus Recovery",
            "title": "Approve 40% discount for 14 portions Paneer Butter Masala",
            "reason": "Lunch window ends in 50 minutes. Batch temperature verified at 65°C. Listing eligible for immediate student marketplace flash sale.",
            "impact": "Recovers ₹1,106 in contribution margin instead of compost write-off",
            "action_label": "Publish to Marketplace",
            "action_route": "/surplus-food"
        },
        {
            "id": "REC-03",
            "priority": "Medium",
            "type": "Procurement Alert",
            "title": "Fresh Paneer stock (14.5 kg) below reorder threshold",
            "reason": "Approved weekly menu requires 32 kg by Friday dinner. Lead time is 1 day.",
            "impact": "Prevents potential lunch service stockout affecting 80+ student meals",
            "action_label": "Review Procurement",
            "action_route": "/inventory"
        }
    ]

    # Nutrition snapshot
    nutrition_snapshot = {
        "average_calories": 520,
        "protein_avg_g": 21.5,
        "carbs_avg_g": 62.0,
        "fat_avg_g": 18.2,
        "dominant_dietary": "Balanced Vegetarian & High-Protein",
        "menu_compliance_score": 96.0
    }

    # Regret Meter
    reporting = ReportingEngine(db)
    regret_data = reporting.get_regret_meter_breakdown(canteen_id, date)

    return {
        "date": date,
        "canteen_id": canteen_id,
        "kpis": {
            "total_prepared": total_prepared,
            "total_sold": total_sold,
            "today_revenue": round(today_revenue, 2),
            "today_cost": round(today_cost, 2),
            "today_profit": today_profit,
            "waste_percentage": waste_percentage,
            "portions_recovered": total_discounted,
            "portions_discarded": total_discarded
        },
        "hourly_performance": hourly_performance,
        "breakdown": breakdown,
        "recommendations": recommendations,
        "nutrition_snapshot": nutrition_snapshot,
        "regret_meter": {
            "score": regret_data["regret_score"],
            "severity": regret_data["severity"],
            "avoidable_loss": regret_data["total_avoidable_loss"],
            "explanation": regret_data["methodology_explanation"]
        }
    }

# --- 2. ANALYTICS CALENDAR ---

@app.get("/api/analytics-calendar")
def get_calendar_overview(
    canteen_id: str = "canteen-1",
    year: int = 2026,
    month: int = 10,
    db: Session = Depends(get_db)
):
    # Fetch all records for this month and canteen
    start_str = f"{year}-{month:02d}-01"
    end_str = f"{year}-{month:02d}-31"

    records = db.query(DailyOperation).filter(
        DailyOperation.canteen_id == canteen_id,
        DailyOperation.date >= start_str,
        DailyOperation.date <= end_str
    ).all()

    by_date: Dict[str, Dict[str, Any]] = {}
    for r in records:
        if r.date not in by_date:
            by_date[r.date] = {
                "date": r.date,
                "revenue": 0.0,
                "cost": 0.0,
                "portions_prepared": 0,
                "portions_sold": 0,
                "portions_discounted": 0,
                "portions_discarded": 0,
                "regret_scores": []
            }
        d = by_date[r.date]
        d["revenue"] += r.revenue
        d["cost"] += r.cost
        d["portions_prepared"] += r.portions_prepared
        d["portions_sold"] += r.portions_sold
        d["portions_discounted"] += r.portions_discounted
        d["portions_discarded"] += r.portions_discarded
        d["regret_scores"].append(r.regret_score)

    calendar_days = []
    for dt_str, data in sorted(by_date.items()):
        prep = data["portions_prepared"]
        disc = data["portions_discarded"]
        waste_pct = round((disc / prep) * 100, 1) if prep > 0 else 0.0
        profit = round(data["revenue"] - data["cost"], 2)
        surplus_recovered_revenue = round(data["portions_discounted"] * 55.0, 2)
        avg_regret = round(float(sum(data["regret_scores"]) / len(data["regret_scores"])), 1) if data["regret_scores"] else 0.0

        calendar_days.append({
            "date": dt_str,
            "has_data": True,
            "revenue": round(data["revenue"], 2),
            "cost": round(data["cost"], 2),
            "profit": profit,
            "portions_prepared": prep,
            "portions_sold": data["portions_sold"],
            "portions_discounted": data["portions_discounted"],
            "portions_discarded": disc,
            "waste_percentage": waste_pct,
            "surplus_recovery_revenue": surplus_recovered_revenue,
            "regret_score": avg_regret
        })

    return {
        "year": year,
        "month": month,
        "canteen_id": canteen_id,
        "recorded_days_count": len(calendar_days),
        "days": calendar_days
    }

@app.get("/api/analytics-calendar/date-detail")
def get_calendar_date_detail(date: str, canteen_id: str = "canteen-1", db: Session = Depends(get_db)):
    records = db.query(DailyOperation).filter(
        DailyOperation.canteen_id == canteen_id,
        DailyOperation.date == date
    ).all()

    if not records:
        return {
            "date": date,
            "has_data": False,
            "message": f"No operational logs recorded for {date} at this location."
        }

    food_items = {f.id: f for f in db.query(FoodItem).all()}

    total_prep = sum(r.portions_prepared for r in records)
    total_sold = sum(r.portions_sold for r in records)
    total_disc = sum(r.portions_discounted for r in records)
    total_discard = sum(r.portions_discarded for r in records)
    total_rev = sum(r.revenue for r in records)
    total_cost = sum(r.cost for r in records)
    profit = round(total_rev - total_cost, 2)
    waste_pct = round((total_discard / total_prep) * 100, 1) if total_prep > 0 else 0.0

    items_detail = []
    for r in records:
        f = food_items.get(r.food_item_id)
        if not f:
            continue
        items_detail.append({
            "food_id": f.id,
            "food_name": f.name,
            "category": f.category,
            "meal_period": r.meal_period,
            "prepared": r.portions_prepared,
            "sold": r.portions_sold,
            "discounted": r.portions_discounted,
            "discarded": r.portions_discarded,
            "revenue": r.revenue,
            "cost": r.cost,
            "waste_percent": r.waste_percent,
            "predicted_demand": r.predicted_demand,
            "unmet_demand": r.unmet_demand,
            "regret_score": r.regret_score
        })

    # Sort items by sales
    sorted_by_sales = sorted(items_detail, key=lambda x: x["sold"], reverse=True)
    best_seller = sorted_by_sales[0] if sorted_by_sales else None
    least_seller = sorted_by_sales[-1] if sorted_by_sales else None

    # Date specific AI notes
    recommendations_for_date = [
        f"Actual demand for {best_seller['food_name'] if best_seller else 'main'} peaked during lunch rush.",
        f"Surplus food recovery prevented {total_disc} portions from going to bio-waste.",
        f"Daily decision regret score maintained at {items_detail[0]['regret_score'] if items_detail else 10}."
    ]

    return {
        "date": date,
        "has_data": True,
        "canteen_id": canteen_id,
        "summary": {
            "portions_prepared": total_prep,
            "portions_sold": total_sold,
            "portions_discounted": total_disc,
            "portions_discarded": total_discard,
            "revenue": round(total_rev, 2),
            "cost": round(total_cost, 2),
            "profit": profit,
            "waste_percentage": waste_pct
        },
        "best_seller": best_seller,
        "least_seller": least_seller,
        "menu_items": items_detail,
        "inventory_issues": [
            "Batter stock was running low before breakfast concluded.",
            "Cold storage temp maintained strictly at 3.8°C throughout shift."
        ],
        "ai_recommendations": recommendations_for_date
    }

# --- 3. DEMAND FORECASTING ---

class ForecastRequest(BaseModel):
    canteen_id: str = "canteen-1"
    target_date: str = "2026-10-30"
    meal_period: str = "All"
    category: str = "All"
    buffer_strategy: str = "balanced" # conservative, balanced, aggressive
    kitchen_capacity: int = 1200

@app.post("/api/forecasting/generate")
def generate_forecast(req: ForecastRequest, db: Session = Depends(get_db)):
    engine = ForecastingEngine(db)
    items = engine.forecast_entire_horizon(
        canteen_id=req.canteen_id,
        start_date=req.target_date,
        days=1,
        meal_period=req.meal_period,
        category=req.category,
        buffer_strategy=req.buffer_strategy,
        kitchen_capacity=req.kitchen_capacity
    )

    # Decision summary
    total_proj_demand = sum(it["predicted_demand"] for it in items)
    total_recommended_prep = sum(it["recommended_prep"] for it in items)
    total_proj_revenue = sum(it["recommended_prep"] * it["base_price"] for it in items)
    total_proj_cost = sum(it["recommended_prep"] * it["prep_cost"] for it in items)
    total_proj_profit = round(total_proj_revenue - total_proj_cost, 2)
    expected_leftovers = max(0, total_recommended_prep - total_proj_demand)

    # Multi-day forecast trend for chart visualization
    trend_horizon = engine.forecast_entire_horizon(
        canteen_id=req.canteen_id,
        start_date=req.target_date,
        days=7,
        meal_period=req.meal_period,
        category=req.category,
        buffer_strategy=req.buffer_strategy,
        kitchen_capacity=req.kitchen_capacity
    )

    # Aggregate by horizon date
    horizon_chart = []
    horizon_by_date: Dict[str, Dict[str, Any]] = {}
    for h in trend_horizon:
        f_date = h["forecast_date"]
        if f_date not in horizon_by_date:
            horizon_by_date[f_date] = {"date": f_date, "predicted_demand": 0, "recommended_prep": 0, "confidence_lower": 0, "confidence_upper": 0}
        horizon_by_date[f_date]["predicted_demand"] += h["predicted_demand"]
        horizon_by_date[f_date]["recommended_prep"] += h["recommended_prep"]
        horizon_by_date[f_date]["confidence_lower"] += h["confidence_lower"]
        horizon_by_date[f_date]["confidence_upper"] += h["confidence_upper"]

    for d_str, v in sorted(horizon_by_date.items()):
        horizon_chart.append(v)

    return {
        "target_date": req.target_date,
        "canteen_id": req.canteen_id,
        "buffer_strategy": req.buffer_strategy,
        "decision_summary": {
            "projected_demand": total_proj_demand,
            "recommended_preparation": total_recommended_prep,
            "projected_revenue": round(total_proj_revenue, 2),
            "projected_ingredient_cost": round(total_proj_cost, 2),
            "projected_profit": total_proj_profit,
            "expected_leftovers_portions": expected_leftovers,
            "potential_unmet_demand_risk": "< 2.8%"
        },
        "forecast_items": items,
        "horizon_chart": horizon_chart
    }

# --- 4. MENU OPTIMIZER ---

class MenuOptimizationRequest(BaseModel):
    canteen_id: str = "canteen-1"
    week_start_date: str = "2026-11-02"
    budget_limit: float = 35000.0
    kitchen_capacity: int = 1200
    priority_profit: float = 0.35
    priority_waste_reduction: float = 0.25
    priority_satisfaction: float = 0.20
    priority_nutrition: float = 0.20
    min_protein_g: float = 16.0
    max_calories: int = 750
    require_vegan_option: bool = True

@app.post("/api/menu-optimizer/optimize")
def optimize_menu(req: MenuOptimizationRequest, db: Session = Depends(get_db)):
    opt = MenuOptimizer(db)
    result = opt.optimize_weekly_menu(
        canteen_id=req.canteen_id,
        week_start_date=req.week_start_date,
        budget_limit=req.budget_limit,
        kitchen_capacity=req.kitchen_capacity,
        priority_profit=req.priority_profit,
        priority_waste_reduction=req.priority_waste_reduction,
        priority_satisfaction=req.priority_satisfaction,
        priority_nutrition=req.priority_nutrition,
        min_protein_g=req.min_protein_g,
        max_calories=req.max_calories,
        require_vegan_option=req.require_vegan_option
    )
    return result

@app.post("/api/menu-optimizer/approve")
def approve_weekly_menu(menu_id: str = "MENU-2026-W45", action: str = "publish", db: Session = Depends(get_db)):
    menu = db.query(WeeklyMenu).filter(WeeklyMenu.id == menu_id).first()
    if not menu:
        # Create or update
        menu = WeeklyMenu(
            id=menu_id,
            week_start_date="2026-11-02",
            canteen_id="canteen-1",
            status="Published" if action == "publish" else "Approved",
            budget_limit=35000.0,
            estimated_cost=29800.0,
            expected_revenue=76100.0,
            expected_profit=46300.0
        )
        db.add(menu)
    else:
        menu.status = "Published" if action == "publish" else "Approved"

    db.commit()
    return {"status": "Success", "menu_id": menu.id, "current_status": menu.status}

# --- 5. SURPLUS FOOD ---

@app.get("/api/surplus/listings")
def get_surplus_listings(canteen_id: Optional[str] = None, active_only: bool = False, db: Session = Depends(get_db)):
    q = db.query(SurplusListing)
    if canteen_id:
        q = q.filter(SurplusListing.canteen_id == canteen_id)
    if active_only:
        q = q.filter(SurplusListing.status == "Active")
    listings = q.all()

    food_items = {f.id: f for f in db.query(FoodItem).all()}

    results = []
    for l in listings:
        f = food_items.get(l.food_item_id)
        results.append({
            "id": l.id,
            "food_item_id": l.food_item_id,
            "food_name": f.name if f else "Surplus Meal",
            "category": f.category if f else "Meal",
            "dietary_type": f.dietary_type if f else "Vegetarian",
            "image_url": f.image_url if f else "",
            "allergens": f.allergens if f else "None",
            "canteen_id": l.canteen_id,
            "batch_code": l.batch_code,
            "portion_size": l.portion_size,
            "quantity_available": l.quantity_available,
            "quantity_reserved": l.quantity_reserved,
            "quantity_sold": l.quantity_sold,
            "quantity_discarded": l.quantity_discarded,
            "original_price": l.original_price,
            "discounted_price": l.discounted_price,
            "discount_percent": l.discount_percent,
            "prep_time": l.prep_time,
            "collection_deadline": l.collection_deadline,
            "safety_status": l.safety_status,
            "status": l.status,
            "disposition_notes": l.disposition_notes
        })
    return results

class CreateSurplusListingRequest(BaseModel):
    food_item_id: str
    canteen_id: str = "canteen-1"
    batch_code: str
    portion_size: str = "Standard Plate"
    quantity: int
    prep_time: str
    collection_deadline: str
    custom_discount_pct: Optional[int] = None
    notes: Optional[str] = ""

@app.post("/api/surplus/listings")
def create_surplus_listing(req: CreateSurplusListingRequest, db: Session = Depends(get_db)):
    engine = SurplusRecoveryEngine(db)
    listing = engine.create_listing(
        food_item_id=req.food_item_id,
        canteen_id=req.canteen_id,
        batch_code=req.batch_code,
        portion_size=req.portion_size,
        quantity=req.quantity,
        prep_time=req.prep_time,
        collection_deadline=req.collection_deadline,
        custom_discount_pct=req.custom_discount_pct,
        notes=req.notes
    )
    return {"status": "Created", "listing_id": listing.id}

class ReserveSurplusRequest(BaseModel):
    listing_id: str
    student_id: str = "STU-DEMO"
    portions: int = 1

@app.post("/api/surplus/reserve")
def reserve_surplus(req: ReserveSurplusRequest, db: Session = Depends(get_db)):
    engine = SurplusRecoveryEngine(db)
    try:
        res = engine.reserve_portions(req.listing_id, req.student_id, req.portions)
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/surplus/confirm-collection")
def confirm_surplus_collection(reservation_id: str, db: Session = Depends(get_db)):
    engine = SurplusRecoveryEngine(db)
    try:
        return engine.confirm_collection(reservation_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/surplus/close")
def close_surplus_listing(listing_id: str, reason: str = "End of Selling Window", db: Session = Depends(get_db)):
    engine = SurplusRecoveryEngine(db)
    try:
        return engine.close_and_record_disposition(listing_id, reason)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/surplus/recommend-discount")
def recommend_discount(food_item_id: str, quantity: int = 15, minutes_until_deadline: int = 90, db: Session = Depends(get_db)):
    engine = SurplusRecoveryEngine(db)
    return engine.calculate_recommended_discount(food_item_id, quantity, minutes_until_deadline)

# --- 6. INVENTORY & PROCUREMENT ---

@app.get("/api/inventory")
def get_inventory(db: Session = Depends(get_db)):
    items = db.query(Ingredient).all()
    return [{
        "id": it.id,
        "name": it.name,
        "category": it.category,
        "current_stock": it.current_stock,
        "unit": it.unit,
        "avg_cost": it.avg_cost,
        "reorder_threshold": it.reorder_threshold,
        "supplier": it.supplier,
        "expiry_date": it.expiry_date,
        "lead_time_days": it.lead_time_days,
        "status": it.status
    } for it in items]

class StockAdjustmentRequest(BaseModel):
    ingredient_id: str
    delta: float
    reason: str = "Daily Kitchen Usage"

@app.post("/api/inventory/adjust-stock")
def adjust_inventory_stock(req: StockAdjustmentRequest, db: Session = Depends(get_db)):
    engine = ProcurementEngine(db)
    try:
        ing = engine.record_stock_adjustment(req.ingredient_id, req.delta, req.reason)
        return {"status": "Updated", "ingredient_id": ing.id, "current_stock": ing.current_stock, "stock_status": ing.status}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/inventory/procurement-recommendations")
def get_procurement_recommendations(menu_id: str = "MENU-2026-W44", db: Session = Depends(get_db)):
    engine = ProcurementEngine(db)
    return engine.calculate_menu_ingredient_demand(menu_id)

class PlaceOrderRequest(BaseModel):
    ingredient_id: str
    quantity: float
    supplier: str
    unit_cost: float

@app.post("/api/inventory/order")
def place_procurement_order(req: PlaceOrderRequest, db: Session = Depends(get_db)):
    engine = ProcurementEngine(db)
    # Update stock as ordered/received
    ing = engine.record_stock_adjustment(req.ingredient_id, req.quantity, "Purchase Delivery")
    return {"status": "Order Placed & Stock Updated", "ingredient_id": ing.id, "new_stock": ing.current_stock}

# --- 7. REPORTS & INSIGHTS ---

@app.get("/api/reports/trends")
def get_report_trends(canteen_id: str = "canteen-1", days: int = 30, db: Session = Depends(get_db)):
    reporting = ReportingEngine(db)
    return reporting.get_performance_trends(canteen_id, days)

@app.get("/api/reports/regret-detail")
def get_regret_detail(canteen_id: str = "canteen-1", date: str = "2026-10-29", db: Session = Depends(get_db)):
    reporting = ReportingEngine(db)
    return reporting.get_regret_meter_breakdown(canteen_id, date)

@app.get("/api/reports/evaluation")
def get_formal_evaluation(canteen_id: str = "canteen-1", db: Session = Depends(get_db)):
    reporting = ReportingEngine(db)
    return reporting.get_before_and_after_evaluation(canteen_id)

# --- 8. SETTINGS ---

@app.get("/api/settings")
def get_settings():
    return {
        "canteen_name": "Central Student Commons",
        "campus_code": "CAMPUS-NORTH",
        "default_capacity": 1400,
        "operating_hours": "07:30 AM - 10:00 PM",
        "buffer_strategy_default": "Balanced (Newsvendor Critical Fractile)",
        "food_safety_max_holding_temp_c": 65,
        "cold_holding_temp_c": 4,
        "max_shelf_life_hours": 4.0,
        "bio_waste_partner": "Campus Green Circular Energy Composting Hub",
        "notification_alerts": {
            "low_stock_sms": True,
            "expiry_warning_hours": 24,
            "surplus_auto_suggest": True
        },
        "role_permissions": {
            "current_user": "Operations Director",
            "role": "Super Admin",
            "can_approve_menus": True,
            "can_override_discounts": True,
            "can_place_po": True
        }
    }
