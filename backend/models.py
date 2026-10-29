from sqlalchemy import Column, Integer, String, Float, Boolean, Date, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class Canteen(Base):
    __tablename__ = "canteens"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    location = Column(String, nullable=False)
    daily_capacity = Column(Integer, default=1200)
    manager_name = Column(String, default="Operations Lead")

class FoodItem(Base):
    __tablename__ = "food_items"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False) # Main, Quick Bite, Healthy, Dessert, Beverage
    meal_period = Column(String, nullable=False) # Breakfast, Lunch, Snacks, Dinner
    base_price = Column(Float, nullable=False)
    prep_cost = Column(Float, nullable=False)
    calories = Column(Integer, nullable=False)
    protein_g = Column(Float, default=15.0)
    carbs_g = Column(Float, default=45.0)
    fat_g = Column(Float, default=12.0)
    allergens = Column(String, default="None")
    shelf_life_hours = Column(Float, default=4.0)
    standard_batch_size = Column(Integer, default=20)
    image_url = Column(String, default="")
    dietary_type = Column(String, default="Vegetarian") # Vegetarian, Non-Vegetarian, Vegan

class Ingredient(Base):
    __tablename__ = "ingredients"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False) # Grain, Protein, Vegetable, Dairy, Spice, Bakery
    current_stock = Column(Float, nullable=False, default=0.0)
    unit = Column(String, nullable=False) # kg, liters, units
    avg_cost = Column(Float, nullable=False) # cost per unit
    reorder_threshold = Column(Float, nullable=False)
    supplier = Column(String, nullable=False)
    expiry_date = Column(String, nullable=False)
    lead_time_days = Column(Integer, default=1)
    status = Column(String, default="Normal") # Normal, Low Stock, Critical, Spoilage Risk

class RecipeItem(Base):
    __tablename__ = "recipe_items"
    id = Column(Integer, primary_key=True, autoincrement=True)
    food_item_id = Column(String, ForeignKey("food_items.id"), nullable=False)
    ingredient_id = Column(String, ForeignKey("ingredients.id"), nullable=False)
    quantity_per_portion = Column(Float, nullable=False)

class DailyOperation(Base):
    __tablename__ = "daily_operations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(String, nullable=False, index=True) # YYYY-MM-DD
    canteen_id = Column(String, ForeignKey("canteens.id"), nullable=False)
    meal_period = Column(String, nullable=False)
    food_item_id = Column(String, ForeignKey("food_items.id"), nullable=False)
    portions_prepared = Column(Integer, nullable=False)
    portions_sold = Column(Integer, nullable=False)
    portions_discounted = Column(Integer, default=0)
    portions_discarded = Column(Integer, default=0)
    unmet_demand = Column(Integer, default=0)
    revenue = Column(Float, nullable=False)
    cost = Column(Float, nullable=False)
    waste_percent = Column(Float, nullable=False)
    regret_score = Column(Float, default=0.0)
    predicted_demand = Column(Integer, default=0)

class ForecastRecord(Base):
    __tablename__ = "forecast_records"
    id = Column(Integer, primary_key=True, autoincrement=True)
    forecast_date = Column(String, nullable=False, index=True)
    canteen_id = Column(String, nullable=False)
    meal_period = Column(String, nullable=False)
    food_item_id = Column(String, ForeignKey("food_items.id"), nullable=False)
    predicted_demand = Column(Integer, nullable=False)
    confidence_lower = Column(Integer, nullable=False)
    confidence_upper = Column(Integer, nullable=False)
    recommended_prep = Column(Integer, nullable=False)
    suggested_buffer = Column(Integer, nullable=False)
    shortage_risk = Column(Float, default=0.0)
    leftover_risk = Column(Float, default=0.0)
    explanation = Column(Text, default="")
    status = Column(String, default="Active")

class WeeklyMenu(Base):
    __tablename__ = "weekly_menus"
    id = Column(String, primary_key=True) # e.g. "WEEK-2026-W44"
    week_start_date = Column(String, nullable=False)
    canteen_id = Column(String, nullable=False)
    status = Column(String, default="Draft") # Draft, Approved, Published
    budget_limit = Column(Float, default=35000.0)
    estimated_cost = Column(Float, default=0.0)
    expected_revenue = Column(Float, default=0.0)
    expected_profit = Column(Float, default=0.0)
    student_satisfaction_score = Column(Float, default=88.5)
    nutrition_compliance = Column(Float, default=94.0)
    surplus_risk_score = Column(Float, default=8.5)
    generated_at = Column(DateTime, default=datetime.utcnow)

class MenuScheduleItem(Base):
    __tablename__ = "menu_schedule_items"
    id = Column(Integer, primary_key=True, autoincrement=True)
    menu_id = Column(String, ForeignKey("weekly_menus.id"), nullable=False)
    day_of_week = Column(String, nullable=False) # Monday, Tuesday, ...
    meal_period = Column(String, nullable=False)
    food_item_id = Column(String, ForeignKey("food_items.id"), nullable=False)
    planned_servings = Column(Integer, nullable=False)

class SurplusListing(Base):
    __tablename__ = "surplus_listings"
    id = Column(String, primary_key=True) # e.g. "SUR-1001"
    food_item_id = Column(String, ForeignKey("food_items.id"), nullable=False)
    canteen_id = Column(String, nullable=False)
    batch_code = Column(String, nullable=False)
    portion_size = Column(String, default="Standard Plate")
    quantity_available = Column(Integer, nullable=False)
    quantity_reserved = Column(Integer, default=0)
    quantity_sold = Column(Integer, default=0)
    quantity_discarded = Column(Integer, default=0)
    original_price = Column(Float, nullable=False)
    discounted_price = Column(Float, nullable=False)
    discount_percent = Column(Integer, nullable=False)
    prep_time = Column(String, nullable=False)
    collection_deadline = Column(String, nullable=False)
    safety_status = Column(String, default="Verified Safe") # Verified Safe, Approaching Limit, Discarded
    status = Column(String, default="Active") # Draft, Active, Reserved, Completed, Expired, Closed
    disposition_notes = Column(String, default="")

class SurplusReservation(Base):
    __tablename__ = "surplus_reservations"
    id = Column(String, primary_key=True) # e.g. "RES-8921"
    listing_id = Column(String, ForeignKey("surplus_listings.id"), nullable=False)
    student_id = Column(String, nullable=False)
    portions = Column(Integer, nullable=False, default=1)
    status = Column(String, default="Reserved") # Reserved, Collected, Cancelled
    created_at = Column(String, default="")
    confirmed_at = Column(String, default="")

class ProcurementRecommendation(Base):
    __tablename__ = "procurement_recommendations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    ingredient_id = Column(String, ForeignKey("ingredients.id"), nullable=False)
    current_stock = Column(Float, nullable=False)
    required_quantity = Column(Float, nullable=False)
    suggested_order = Column(Float, nullable=False)
    unit = Column(String, nullable=False)
    supplier = Column(String, nullable=False)
    estimated_cost = Column(Float, nullable=False)
    urgency = Column(String, default="Medium") # Urgent, High, Medium, Low
    reason = Column(Text, default="")
    status = Column(String, default="Pending") # Pending, Approved, Ordered, Received
