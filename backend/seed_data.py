import random
from datetime import datetime, timedelta
from database import engine, SessionLocal, Base
from models import (
    Canteen, FoodItem, Ingredient, RecipeItem,
    DailyOperation, ForecastRecord, WeeklyMenu,
    MenuScheduleItem, SurplusListing, SurplusReservation,
    ProcurementRecommendation
)

def init_db():
    Base.metadata.create_all(bind=engine)

def seed_data():
    db = SessionLocal()
    # Check if already seeded
    if db.query(Canteen).first():
        print("Database already seeded.")
        db.close()
        return

    print("Seeding CanteenIQ enterprise database...")

    # 1. Canteens
    canteens = [
        Canteen(id="canteen-1", name="Central Student Commons", location="Main Campus Center, Block A", daily_capacity=1400, manager_name="Priya Sharma"),
        Canteen(id="canteen-2", name="Engineering Quad Cafeteria", location="Tech Wing 3, Ground Floor", daily_capacity=950, manager_name="David Chen"),
        Canteen(id="canteen-3", name="Graduate Hall Bistro", location="Grad Residence Quad, Tower C", daily_capacity=600, manager_name="Amina Al-Mansoor"),
    ]
    for c in canteens:
        db.add(c)
    db.commit()

    # 2. Food Items
    food_items = [
        # Breakfast
        FoodItem(id="FOOD-01", name="Masala Dosa with Sambar & Chutney", category="Main", meal_period="Breakfast", base_price=65.0, prep_cost=26.0, calories=380, protein_g=8.5, carbs_g=58.0, fat_g=11.0, allergens="Dairy (Ghee)", shelf_life_hours=3.0, standard_batch_size=25, dietary_type="Vegetarian", image_url="https://images.unsplash.com/photo-1589301760014-d929f3979dbc?w=600&auto=format&fit=crop&q=80"),
        FoodItem(id="FOOD-02", name="Steamed Idli & Crispy Medu Vada", category="Main", meal_period="Breakfast", base_price=55.0, prep_cost=21.0, calories=320, protein_g=9.0, carbs_g=52.0, fat_g=7.5, allergens="None", shelf_life_hours=4.0, standard_batch_size=30, dietary_type="Vegetarian", image_url="https://images.unsplash.com/photo-1589301760014-d929f3979dbc?w=600&auto=format&fit=crop&q=80"),
        FoodItem(id="FOOD-03", name="Warm Poha with Roasted Peanuts", category="Quick Bite", meal_period="Breakfast", base_price=40.0, prep_cost=14.0, calories=260, protein_g=6.2, carbs_g=44.0, fat_g=6.0, allergens="Peanuts", shelf_life_hours=3.5, standard_batch_size=35, dietary_type="Vegan", image_url="https://images.unsplash.com/photo-1626777552726-4a6b54c97e46?w=600&auto=format&fit=crop&q=80"),
        FoodItem(id="FOOD-04", name="Egg & Cheese Brioche Breakfast Roll", category="Main", meal_period="Breakfast", base_price=75.0, prep_cost=31.0, calories=410, protein_g=19.0, carbs_g=36.0, fat_g=21.0, allergens="Egg, Dairy, Gluten", shelf_life_hours=3.0, standard_batch_size=20, dietary_type="Non-Vegetarian", image_url="https://images.unsplash.com/photo-1525351484163-7529414344d8?w=600&auto=format&fit=crop&q=80"),

        # Lunch
        FoodItem(id="FOOD-05", name="Royal Chicken Dum Biryani Box", category="Main", meal_period="Lunch", base_price=165.0, prep_cost=68.0, calories=740, protein_g=34.0, carbs_g=82.0, fat_g=26.0, allergens="Dairy (Curd)", shelf_life_hours=4.0, standard_batch_size=40, dietary_type="Non-Vegetarian", image_url="https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=600&auto=format&fit=crop&q=80"),
        FoodItem(id="FOOD-06", name="Paneer Butter Masala Deluxe Thali", category="Main", meal_period="Lunch", base_price=135.0, prep_cost=54.0, calories=690, protein_g=23.0, carbs_g=78.0, fat_g=29.0, allergens="Dairy, Gluten", shelf_life_hours=4.0, standard_batch_size=35, dietary_type="Vegetarian", image_url="https://images.unsplash.com/photo-1631452180519-c014fe946bc7?w=600&auto=format&fit=crop&q=80"),
        FoodItem(id="FOOD-07", name="Dal Tadka with Steamed Basmati Rice", category="Main", meal_period="Lunch", base_price=95.0, prep_cost=34.0, calories=520, protein_g=16.0, carbs_g=84.0, fat_g=12.0, allergens="None", shelf_life_hours=4.5, standard_batch_size=40, dietary_type="Vegan", image_url="https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=600&auto=format&fit=crop&q=80"),
        FoodItem(id="FOOD-08", name="Mediterranean Falafel & Tahini Bowl", category="Healthy", meal_period="Lunch", base_price=145.0, prep_cost=58.0, calories=470, protein_g=18.0, carbs_g=54.0, fat_g=17.0, allergens="Sesame", shelf_life_hours=4.0, standard_batch_size=20, dietary_type="Vegan", image_url="https://images.unsplash.com/photo-1540420773420-3366772f4999?w=600&auto=format&fit=crop&q=80"),

        # Snacks
        FoodItem(id="FOOD-09", name="Crispy Delhi Samosa Chaat", category="Quick Bite", meal_period="Snacks", base_price=50.0, prep_cost=17.0, calories=340, protein_g=7.0, carbs_g=46.0, fat_g=14.0, allergens="Gluten, Dairy", shelf_life_hours=3.0, standard_batch_size=30, dietary_type="Vegetarian", image_url="https://images.unsplash.com/photo-1601050690597-df0568f70950?w=600&auto=format&fit=crop&q=80"),
        FoodItem(id="FOOD-10", name="Spinach & Golden Corn Baked Puff", category="Quick Bite", meal_period="Snacks", base_price=45.0, prep_cost=16.0, calories=280, protein_g=6.5, carbs_g=34.0, fat_g=13.0, allergens="Gluten, Dairy", shelf_life_hours=4.0, standard_batch_size=30, dietary_type="Vegetarian", image_url="https://images.unsplash.com/photo-1509440159596-0249088772ff?w=600&auto=format&fit=crop&q=80"),
        FoodItem(id="FOOD-11", name="Greek Blueberry Yogurt Crunch", category="Healthy", meal_period="Snacks", base_price=85.0, prep_cost=34.0, calories=220, protein_g=15.0, carbs_g=26.0, fat_g=4.5, allergens="Dairy, Nuts", shelf_life_hours=5.0, standard_batch_size=25, dietary_type="Vegetarian", image_url="https://images.unsplash.com/photo-1488477181946-6428a0291777?w=600&auto=format&fit=crop&q=80"),
        FoodItem(id="FOOD-12", name="Ginger Cardamom Masala Chai Combo", category="Beverage", meal_period="Snacks", base_price=30.0, prep_cost=9.0, calories=130, protein_g=3.2, carbs_g=21.0, fat_g=3.8, allergens="Dairy", shelf_life_hours=2.5, standard_batch_size=50, dietary_type="Vegetarian", image_url="https://images.unsplash.com/photo-1576092768241-dec231879fc3?w=600&auto=format&fit=crop&q=80"),

        # Dinner
        FoodItem(id="FOOD-13", name="Butter Chicken with Tandoori Naan", category="Main", meal_period="Dinner", base_price=175.0, prep_cost=74.0, calories=770, protein_g=38.0, carbs_g=66.0, fat_g=36.0, allergens="Dairy, Gluten", shelf_life_hours=4.0, standard_batch_size=35, dietary_type="Non-Vegetarian", image_url="https://images.unsplash.com/photo-1588166524941-3bf61a9c41db?w=600&auto=format&fit=crop&q=80"),
        FoodItem(id="FOOD-14", name="Homestyle Rajma & Jeera Rice Bowl", category="Main", meal_period="Dinner", base_price=105.0, prep_cost=39.0, calories=550, protein_g=18.5, carbs_g=86.0, fat_g=11.5, allergens="None", shelf_life_hours=4.0, standard_batch_size=40, dietary_type="Vegan", image_url="https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=600&auto=format&fit=crop&q=80"),
        FoodItem(id="FOOD-15", name="Wok Charred Tofu & Brown Rice Bowl", category="Healthy", meal_period="Dinner", base_price=140.0, prep_cost=53.0, calories=480, protein_g=24.0, carbs_g=56.0, fat_g=13.0, allergens="Soy", shelf_life_hours=4.0, standard_batch_size=25, dietary_type="Vegan", image_url="https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=600&auto=format&fit=crop&q=80"),
        FoodItem(id="FOOD-16", name="Garden Herb Penne Primavera", category="Main", meal_period="Dinner", base_price=130.0, prep_cost=49.0, calories=520, protein_g=14.0, carbs_g=74.0, fat_g=17.0, allergens="Gluten, Dairy", shelf_life_hours=3.5, standard_batch_size=30, dietary_type="Vegetarian", image_url="https://images.unsplash.com/photo-1621996346565-e3d5d6281691?w=600&auto=format&fit=crop&q=80"),
    ]
    for item in food_items:
        db.add(item)
    db.commit()

    # 3. Ingredients
    ingredients = [
        Ingredient(id="ING-01", name="Basmati Rice (Grade A)", category="Grain", current_stock=185.0, unit="kg", avg_cost=72.0, reorder_threshold=50.0, supplier="Punjab Agro Millers", expiry_date="2026-12-15", lead_time_days=2, status="Normal"),
        Ingredient(id="ING-02", name="Fresh Paneer (Cottage Cheese)", category="Dairy", current_stock=14.5, unit="kg", avg_cost=310.0, reorder_threshold=20.0, supplier="Heritage Dairy Farms", expiry_date="2026-10-31", lead_time_days=1, status="Low Stock"),
        Ingredient(id="ING-03", name="Boneless Farm Chicken", category="Protein", current_stock=38.0, unit="kg", avg_cost=240.0, reorder_threshold=25.0, supplier="Apex Poultry Ltd", expiry_date="2026-10-31", lead_time_days=1, status="Normal"),
        Ingredient(id="ING-04", name="Red Kidney Beans (Rajma)", category="Grain", current_stock=45.0, unit="kg", avg_cost=125.0, reorder_threshold=15.0, supplier="Northern Pulses Co", expiry_date="2027-02-20", lead_time_days=3, status="Normal"),
        Ingredient(id="ING-05", name="Yellow Toor Dal", category="Grain", current_stock=52.0, unit="kg", avg_cost=145.0, reorder_threshold=20.0, supplier="Northern Pulses Co", expiry_date="2027-01-10", lead_time_days=2, status="Normal"),
        Ingredient(id="ING-06", name="Dosa Batter (Fermented)", category="Bakery", current_stock=8.0, unit="kg", avg_cost=55.0, reorder_threshold=15.0, supplier="South Spices Kitchen", expiry_date="2026-10-30", lead_time_days=1, status="Low Stock"),
        Ingredient(id="ING-07", name="Fresh Eggs (Crate 30s)", category="Protein", current_stock=18.0, unit="crates", avg_cost=180.0, reorder_threshold=10.0, supplier="Apex Poultry Ltd", expiry_date="2026-11-08", lead_time_days=1, status="Normal"),
        Ingredient(id="ING-08", name="Organic Firm Tofu", category="Protein", current_stock=5.0, unit="kg", avg_cost=210.0, reorder_threshold=8.0, supplier="GreenLife Organics", expiry_date="2026-11-03", lead_time_days=2, status="Critical"),
        Ingredient(id="ING-09", name="Cooking Butter / Ghee", category="Dairy", current_stock=22.0, unit="kg", avg_cost=540.0, reorder_threshold=10.0, supplier="Heritage Dairy Farms", expiry_date="2026-12-01", lead_time_days=1, status="Normal"),
        Ingredient(id="ING-10", name="Yellow Onions & Fresh Garlic", category="Vegetable", current_stock=75.0, unit="kg", avg_cost=38.0, reorder_threshold=30.0, supplier="Metro Produce Hub", expiry_date="2026-11-12", lead_time_days=1, status="Normal"),
        Ingredient(id="ING-11", name="Ripe Roma Tomatoes", category="Vegetable", current_stock=12.0, unit="kg", avg_cost=42.0, reorder_threshold=25.0, supplier="Metro Produce Hub", expiry_date="2026-11-02", lead_time_days=1, status="Low Stock"),
        Ingredient(id="ING-12", name="Chickpeas (Kabuli Chana)", category="Grain", current_stock=30.0, unit="kg", avg_cost=110.0, reorder_threshold=15.0, supplier="Northern Pulses Co", expiry_date="2027-03-01", lead_time_days=2, status="Normal"),
        Ingredient(id="ING-13", name="Penne Durum Wheat Pasta", category="Grain", current_stock=28.0, unit="kg", avg_cost=160.0, reorder_threshold=12.0, supplier="Global Foods Corp", expiry_date="2027-06-15", lead_time_days=3, status="Normal"),
        Ingredient(id="ING-14", name="Greek Style Plain Yogurt", category="Dairy", current_stock=6.5, unit="kg", avg_cost=190.0, reorder_threshold=10.0, supplier="Heritage Dairy Farms", expiry_date="2026-11-01", lead_time_days=1, status="Critical"),
        Ingredient(id="ING-15", name="Fresh Milk (Full Cream)", category="Dairy", current_stock=35.0, unit="liters", avg_cost=62.0, reorder_threshold=20.0, supplier="Heritage Dairy Farms", expiry_date="2026-10-31", lead_time_days=1, status="Normal"),
    ]
    for ing in ingredients:
        db.add(ing)
    db.commit()

    # 4. Recipe mapping
    recipes = [
        # Biryani
        RecipeItem(food_item_id="FOOD-05", ingredient_id="ING-01", quantity_per_portion=0.18), # 180g rice
        RecipeItem(food_item_id="FOOD-05", ingredient_id="ING-03", quantity_per_portion=0.16), # 160g chicken
        RecipeItem(food_item_id="FOOD-05", ingredient_id="ING-09", quantity_per_portion=0.03), # 30g ghee
        RecipeItem(food_item_id="FOOD-05", ingredient_id="ING-10", quantity_per_portion=0.08), # onion
        # Paneer Thali
        RecipeItem(food_item_id="FOOD-06", ingredient_id="ING-02", quantity_per_portion=0.12), # 120g paneer
        RecipeItem(food_item_id="FOOD-06", ingredient_id="ING-01", quantity_per_portion=0.14), # rice
        RecipeItem(food_item_id="FOOD-06", ingredient_id="ING-11", quantity_per_portion=0.10), # tomato
        RecipeItem(food_item_id="FOOD-06", ingredient_id="ING-09", quantity_per_portion=0.025), # butter
        # Butter Chicken
        RecipeItem(food_item_id="FOOD-13", ingredient_id="ING-03", quantity_per_portion=0.18), # chicken
        RecipeItem(food_item_id="FOOD-13", ingredient_id="ING-09", quantity_per_portion=0.04), # butter
        RecipeItem(food_item_id="FOOD-13", ingredient_id="ING-11", quantity_per_portion=0.12), # tomato
        # Rajma Chawal
        RecipeItem(food_item_id="FOOD-14", ingredient_id="ING-04", quantity_per_portion=0.12), # rajma
        RecipeItem(food_item_id="FOOD-14", ingredient_id="ING-01", quantity_per_portion=0.15), # rice
        RecipeItem(food_item_id="FOOD-14", ingredient_id="ING-10", quantity_per_portion=0.06), # onion
        # Dal Tadka
        RecipeItem(food_item_id="FOOD-07", ingredient_id="ING-05", quantity_per_portion=0.10), # toor dal
        RecipeItem(food_item_id="FOOD-07", ingredient_id="ING-01", quantity_per_portion=0.15), # rice
        RecipeItem(food_item_id="FOOD-07", ingredient_id="ING-09", quantity_per_portion=0.015), # ghee
        # Dosa
        RecipeItem(food_item_id="FOOD-01", ingredient_id="ING-06", quantity_per_portion=0.22), # batter
        RecipeItem(food_item_id="FOOD-01", ingredient_id="ING-09", quantity_per_portion=0.015), # ghee
        # Tofu Bowl
        RecipeItem(food_item_id="FOOD-15", ingredient_id="ING-08", quantity_per_portion=0.14), # tofu
        RecipeItem(food_item_id="FOOD-15", ingredient_id="ING-01", quantity_per_portion=0.12), # rice
    ]
    for r in recipes:
        db.add(r)
    db.commit()

    # 5. Historical Daily Operations: 60 Days up to today (October 29, 2026)
    today = datetime(2026, 10, 29)
    food_lookup = {item.id: item for item in food_items}

    # Deterministic seed for realism
    rng = random.Random(42)

    for days_ago in range(60, -1, -1):
        cur_date = (today - timedelta(days=days_ago)).strftime("%Y-%m-%d")
        day_of_week = (today - timedelta(days=days_ago)).weekday() # 0 = Monday, 6 = Sunday
        is_weekend = day_of_week >= 5

        # Attendance factor: weekdays ~1.0, weekends ~0.45
        attendance_mult = 0.45 if is_weekend else (1.0 + (day_of_week % 3) * 0.05)

        # Operational improvement factor over time: older days had worse waste (12-18%), recent days improved (3-6%)
        learning_factor = max(0.25, (days_ago / 60.0)) # 1.0 (60 days ago) down to 0.25 (today)

        for canteen in canteens:
            canteen_mult = 1.0 if canteen.id == "canteen-1" else (0.7 if canteen.id == "canteen-2" else 0.45)

            # Pick 6-8 items served each day
            served_items = [
                "FOOD-01", "FOOD-03", # Breakfast
                "FOOD-05", "FOOD-06", "FOOD-07", # Lunch
                "FOOD-09", "FOOD-11", # Snacks
                "FOOD-13", "FOOD-14", "FOOD-15" # Dinner
            ]

            for fid in served_items:
                item = food_lookup[fid]
                base_demand = int(item.standard_batch_size * 2.8 * attendance_mult * canteen_mult)
                # Random variation +/- 15%
                actual_demand = max(10, int(base_demand * (0.85 + rng.random() * 0.30)))

                # Preparation strategy
                # Earlier days: overproduced heavily or ran short
                overprep_bias = int(actual_demand * (0.05 + 0.15 * learning_factor * rng.random()))
                prepared = actual_demand + overprep_bias

                # Sold is bounded by demand and prepared
                sold = min(prepared, actual_demand)
                leftover = prepared - sold

                # In recent days, surplus recovery is high; in old days, mostly discarded
                recovery_rate = (1.0 - learning_factor) * 0.70 # up to 70% surplus recovered via discount
                discounted = int(leftover * recovery_rate) if leftover > 0 else 0
                discarded = leftover - discounted

                # Exact arithmetic
                # discount price is ~40% off base
                disc_price = round(item.base_price * 0.60, 2)
                revenue = round((sold * item.base_price) + (discounted * disc_price), 2)
                cost = round(prepared * item.prep_cost, 2)
                waste_pct = round((discarded / prepared) * 100.0, 1) if prepared > 0 else 0.0

                # Regret meter formula:
                # Avoidable loss = (discarded * prep_cost) + (unmet_demand * (base_price - prep_cost)) + margin shortfall on surplus
                unmet = max(0, actual_demand - prepared)
                avoidable_loss = (discarded * item.prep_cost) + (unmet * (item.base_price - item.prep_cost)) + (discounted * (item.base_price - disc_price) * 0.3)
                # Normalize regret score (0-100)
                regret_score = min(100.0, round((avoidable_loss / (prepared * item.base_price * 0.25)) * 100, 1)) if prepared > 0 else 0.0

                predicted = int(base_demand * (0.95 + rng.random() * 0.10))

                op = DailyOperation(
                    date=cur_date,
                    canteen_id=canteen.id,
                    meal_period=item.meal_period,
                    food_item_id=item.id,
                    portions_prepared=prepared,
                    portions_sold=sold,
                    portions_discounted=discounted,
                    portions_discarded=discarded,
                    unmet_demand=unmet,
                    revenue=revenue,
                    cost=cost,
                    waste_percent=waste_pct,
                    regret_score=regret_score,
                    predicted_demand=predicted
                )
                db.add(op)

    db.commit()

    # 6. Forecast Records for Tomorrow (2026-10-30) and the upcoming weekend
    forecast_dates = ["2026-10-30", "2026-10-31", "2026-11-01"]
    for f_date in forecast_dates:
        for canteen in canteens:
            for item in food_items:
                dow = datetime.strptime(f_date, "%Y-%m-%d").weekday()
                is_wknd = dow >= 5
                c_mult = 1.0 if canteen.id == "canteen-1" else (0.7 if canteen.id == "canteen-2" else 0.45)
                base = int(item.standard_batch_size * 2.8 * (0.5 if is_wknd else 1.05) * c_mult)

                pred_demand = max(12, int(base * (0.92 + rng.random() * 0.16)))
                # Confidence interval +/- 12%
                c_lower = int(pred_demand * 0.88)
                c_upper = int(pred_demand * 1.14)

                # Buffer calculation using Newsvendor critical fractile ratio:
                # Cu = (Price - Cost), Co = Cost
                # ratio = Cu / (Cu + Co)
                cu = item.base_price - item.prep_cost
                co = item.prep_cost
                critical_ratio = cu / (cu + co)
                # buffer portions based on critical fractile
                buffer = max(2, int((c_upper - pred_demand) * critical_ratio * 0.65))
                recommended = pred_demand + buffer

                # Capacity check (e.g. limit to batch multiples)
                batch_mult = item.standard_batch_size
                recommended_batch = ((recommended + batch_mult - 1) // batch_mult) * batch_mult

                shortage_risk = round((1.0 - critical_ratio) * 15.0 + rng.random() * 4, 1)
                leftover_risk = round(critical_ratio * 12.0 + rng.random() * 3, 1)

                exp = f"Based on 60-day historical trend for {item.meal_period} and Friday traffic, demand is projected at {pred_demand} units. Critical ratio is {critical_ratio:.2f}. Recommend {recommended_batch} units (Batch of {batch_mult}) with a staged {buffer}-portion safety buffer to keep stockout risk < {shortage_risk}%."

                f_rec = ForecastRecord(
                    forecast_date=f_date,
                    canteen_id=canteen.id,
                    meal_period=item.meal_period,
                    food_item_id=item.id,
                    predicted_demand=pred_demand,
                    confidence_lower=c_lower,
                    confidence_upper=c_upper,
                    recommended_prep=recommended_batch,
                    suggested_buffer=buffer,
                    shortage_risk=shortage_risk,
                    leftover_risk=leftover_risk,
                    explanation=exp
                )
                db.add(f_rec)
    db.commit()

    # 7. Active Surplus Listings for Today (October 29, 2026)
    surplus_data = [
        SurplusListing(
            id="SUR-1041",
            food_item_id="FOOD-05", # Biryani
            canteen_id="canteen-1",
            batch_code="B-LUNCH-29A",
            portion_size="Regular Meal Box (450g)",
            quantity_available=18,
            quantity_reserved=6,
            quantity_sold=4,
            quantity_discarded=0,
            original_price=165.0,
            discounted_price=99.0,
            discount_percent=40,
            prep_time="12:15 PM",
            collection_deadline="03:45 PM",
            safety_status="Verified Safe",
            status="Active",
            disposition_notes="Fresh hot-holding verified at 68°C. Safe window until 4:00 PM."
        ),
        SurplusListing(
            id="SUR-1042",
            food_item_id="FOOD-06", # Paneer Thali
            canteen_id="canteen-1",
            batch_code="B-LUNCH-29B",
            portion_size="Thali Combo Plate",
            quantity_available=14,
            quantity_reserved=5,
            quantity_sold=3,
            quantity_discarded=0,
            original_price=135.0,
            discounted_price=79.0,
            discount_percent=41,
            prep_time="12:30 PM",
            collection_deadline="03:30 PM",
            safety_status="Verified Safe",
            status="Active",
            disposition_notes="Maintained at 65°C steam table. 1-hour countdown to close."
        ),
        SurplusListing(
            id="SUR-1043",
            food_item_id="FOOD-08", # Falafel Bowl
            canteen_id="canteen-2",
            batch_code="B-LUNCH-29C",
            portion_size="Chilled Salad Box",
            quantity_available=9,
            quantity_reserved=2,
            quantity_sold=1,
            quantity_discarded=0,
            original_price=145.0,
            discounted_price=85.0,
            discount_percent=41,
            prep_time="12:00 PM",
            collection_deadline="03:30 PM",
            safety_status="Verified Safe",
            status="Active",
            disposition_notes="Cold display at 4°C. Allergen label verified."
        ),
        SurplusListing(
            id="SUR-1044",
            food_item_id="FOOD-01", # Dosa (from breakfast)
            canteen_id="canteen-1",
            batch_code="B-BKFST-29A",
            portion_size="Quick Snack Pack",
            quantity_available=0,
            quantity_reserved=0,
            quantity_sold=8,
            quantity_discarded=2,
            original_price=65.0,
            discounted_price=35.0,
            discount_percent=46,
            prep_time="09:15 AM",
            collection_deadline="11:30 AM",
            safety_status="Approaching Limit",
            status="Closed",
            disposition_notes="Window ended at 11:30 AM. 2 unsold portions composted per campus green audit."
        ),
    ]
    for s in surplus_data:
        db.add(s)
    db.commit()

    # Active reservations for demo
    res1 = SurplusReservation(
        id="RES-4821",
        listing_id="SUR-1041",
        student_id="STU-2024-8841",
        portions=2,
        status="Reserved",
        created_at="01:15 PM"
    )
    res2 = SurplusReservation(
        id="RES-4822",
        listing_id="SUR-1042",
        student_id="STU-2024-9102",
        portions=1,
        status="Reserved",
        created_at="01:22 PM"
    )
    db.add(res1)
    db.add(res2)
    db.commit()

    # 8. Weekly Menus (Current approved & next week draft)
    menu_curr = WeeklyMenu(
        id="MENU-2026-W44",
        week_start_date="2026-10-26",
        canteen_id="canteen-1",
        status="Published",
        budget_limit=45000.0,
        estimated_cost=31200.0,
        expected_revenue=78400.0,
        expected_profit=47200.0,
        student_satisfaction_score=91.4,
        nutrition_compliance=96.0,
        surplus_risk_score=5.2
    )
    db.add(menu_curr)

    menu_next = WeeklyMenu(
        id="MENU-2026-W45",
        week_start_date="2026-11-02",
        canteen_id="canteen-1",
        status="Draft",
        budget_limit=45000.0,
        estimated_cost=29800.0,
        expected_revenue=76100.0,
        expected_profit=46300.0,
        student_satisfaction_score=89.8,
        nutrition_compliance=94.5,
        surplus_risk_score=6.0
    )
    db.add(menu_next)
    db.commit()

    # Menu schedule items for days of week
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    meal_assignments = [
        ("Breakfast", ["FOOD-01", "FOOD-03"]),
        ("Lunch", ["FOOD-05", "FOOD-06", "FOOD-07"]),
        ("Snacks", ["FOOD-09", "FOOD-11"]),
        ("Dinner", ["FOOD-13", "FOOD-14"]),
    ]
    for d in days:
        for meal, items in meal_assignments:
            for item_id in items:
                db.add(MenuScheduleItem(
                    menu_id="MENU-2026-W44",
                    day_of_week=d,
                    meal_period=meal,
                    food_item_id=item_id,
                    planned_servings=80 if meal == "Lunch" else 50
                ))
                db.add(MenuScheduleItem(
                    menu_id="MENU-2026-W45",
                    day_of_week=d,
                    meal_period=meal,
                    food_item_id=item_id,
                    planned_servings=75 if meal == "Lunch" else 45
                ))
    db.commit()

    # 9. Procurement Recommendations
    recs = [
        ProcurementRecommendation(
            ingredient_id="ING-02", # Fresh Paneer
            current_stock=14.5,
            required_quantity=32.0,
            suggested_order=25.0,
            unit="kg",
            supplier="Heritage Dairy Farms",
            estimated_cost=7750.0,
            urgency="Urgent",
            reason="Required for Friday lunch Paneer Butter Masala. Current stock (14.5 kg) is below reorder threshold (20 kg) and menu requires 18 kg tomorrow.",
            status="Pending"
        ),
        ProcurementRecommendation(
            ingredient_id="ING-08", # Firm Tofu
            current_stock=5.0,
            required_quantity=14.0,
            suggested_order=10.0,
            unit="kg",
            supplier="GreenLife Organics",
            estimated_cost=2100.0,
            urgency="High",
            reason="Current stock at 5 kg is critical. Planned dinner bowl requires 7 kg on Friday.",
            status="Pending"
        ),
        ProcurementRecommendation(
            ingredient_id="ING-11", # Roma Tomatoes
            current_stock=12.0,
            required_quantity=35.0,
            suggested_order=30.0,
            unit="kg",
            supplier="Metro Produce Hub",
            estimated_cost=1260.0,
            urgency="High",
            reason="Stock depletion anticipated by Thursday dinner gravy bases.",
            status="Pending"
        ),
        ProcurementRecommendation(
            ingredient_id="ING-06", # Dosa Batter
            current_stock=8.0,
            required_quantity=22.0,
            suggested_order=20.0,
            unit="kg",
            supplier="South Spices Kitchen",
            estimated_cost=1100.0,
            urgency="Medium",
            reason="Daily morning replenishment to guarantee fermented consistency.",
            status="Approved"
        ),
    ]
    for r in recs:
        db.add(r)
    db.commit()

    print("Database seeding completed successfully.")
    db.close()

if __name__ == "__main__":
    init_db()
    seed_data()
