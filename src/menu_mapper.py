"""Menu mapping and synthetic canteen catalog definition for MenuMind."""

from typing import Dict, Any, Tuple
import pandas as pd
import numpy as np


SYNTHETIC_DISH_CATALOG: Dict[int, Dict[str, Any]] = {
    # --- Beverages (12 items) ---
    1885: {"name": "Thai Lemongrass Iced Tea", "calories": 160, "rating": 4.6, "cost_ratio": 0.40, "elasticity": -1.2},
    1993: {"name": "Spiced Thai Milk Tea", "calories": 210, "rating": 4.5, "cost_ratio": 0.42, "elasticity": -1.1},
    2539: {"name": "Sparkling Lychee Basil Cooler", "calories": 140, "rating": 4.3, "cost_ratio": 0.38, "elasticity": -1.3},
    1248: {"name": "Masala Chai Kettle (Serves 2)", "calories": 120, "rating": 4.8, "cost_ratio": 0.35, "elasticity": -0.8},
    2139: {"name": "Fresh Alphonso Mango Lassi", "calories": 260, "rating": 4.7, "cost_ratio": 0.45, "elasticity": -1.0},
    2631: {"name": "South Indian Filter Coffee", "calories": 130, "rating": 4.8, "cost_ratio": 0.36, "elasticity": -0.7},
    1062: {"name": "Espresso Freddo Tonic", "calories": 85, "rating": 4.4, "cost_ratio": 0.40, "elasticity": -1.1},
    1778: {"name": "Iced Caramel Macchiato", "calories": 240, "rating": 4.6, "cost_ratio": 0.42, "elasticity": -1.2},
    2707: {"name": "Classic Cold Hazelnut Mocha", "calories": 280, "rating": 4.7, "cost_ratio": 0.44, "elasticity": -1.1},
    1207: {"name": "Classic Vanilla Bean Milkshake", "calories": 320, "rating": 4.3, "cost_ratio": 0.45, "elasticity": -1.0},
    1230: {"name": "Cold Brew Black Roast Coffee", "calories": 15, "rating": 4.5, "cost_ratio": 0.38, "elasticity": -0.9},
    2322: {"name": "Belgian Chocolate Frappe", "calories": 360, "rating": 4.7, "cost_ratio": 0.46, "elasticity": -1.2},

    # --- Rice Bowls (3 items) ---
    1109: {"name": "Paneer Butter Masala Rice Bowl", "calories": 580, "rating": 4.7, "cost_ratio": 0.48, "elasticity": -0.7},
    1727: {"name": "Shahi Paneer Biryani Bowl", "calories": 620, "rating": 4.6, "cost_ratio": 0.50, "elasticity": -0.8},
    2290: {"name": "Dal Tadka & Jeera Rice Comfort Bowl", "calories": 480, "rating": 4.8, "cost_ratio": 0.42, "elasticity": -0.6},

    # --- Biryani (3 items) ---
    1247: {"name": "Lucknowi Subz Dum Biryani", "calories": 560, "rating": 4.4, "cost_ratio": 0.50, "elasticity": -0.8},
    1770: {"name": "Spiced Egg Dum Biryani Platter", "calories": 610, "rating": 4.5, "cost_ratio": 0.48, "elasticity": -0.8},
    1902: {"name": "Hyderabadi Veg Dum Biryani", "calories": 590, "rating": 4.6, "cost_ratio": 0.49, "elasticity": -0.8},

    # --- Sandwiches (3 items) ---
    1754: {"name": "Pesto Veggie Grilled Panini", "calories": 410, "rating": 4.6, "cost_ratio": 0.45, "elasticity": -1.0},
    1971: {"name": "Three-Cheese Herb Toasted Ciabatta", "calories": 460, "rating": 4.7, "cost_ratio": 0.47, "elasticity": -1.0},
    2826: {"name": "Spicy Paneer Tikka Focaccia Melt", "calories": 490, "rating": 4.6, "cost_ratio": 0.46, "elasticity": -0.9},

    # --- Salads (3 items) ---
    2490: {"name": "Classic Tuscan Caesar Salad", "calories": 210, "rating": 4.4, "cost_ratio": 0.46, "elasticity": -1.1},
    2569: {"name": "Balsamic Caprese Pasta Salad", "calories": 340, "rating": 4.3, "cost_ratio": 0.48, "elasticity": -1.0},
    2664: {"name": "Mediterranean Quinoa Green Salad", "calories": 280, "rating": 4.5, "cost_ratio": 0.47, "elasticity": -1.1},

    # --- Pizzas (3 items) ---
    1558: {"name": "Classic Margherita Stone-Baked Pizza", "calories": 620, "rating": 4.6, "cost_ratio": 0.46, "elasticity": -1.2},
    1962: {"name": "Smoky Paneer & Roasted Paprika Pizza", "calories": 710, "rating": 4.7, "cost_ratio": 0.48, "elasticity": -1.1},
    2581: {"name": "Farmhouse Veggie Supreme Pizza", "calories": 680, "rating": 4.5, "cost_ratio": 0.47, "elasticity": -1.1},

    # --- Pastas (3 items) ---
    1216: {"name": "Cheesy Alfredo Fusilli Pasta", "calories": 540, "rating": 4.4, "cost_ratio": 0.46, "elasticity": -1.1},
    2126: {"name": "Baked Spinach & Ricotta Lasagna", "calories": 580, "rating": 4.5, "cost_ratio": 0.50, "elasticity": -1.0},
    2306: {"name": "Creamy Tomato Penne Arrabbiata", "calories": 470, "rating": 4.3, "cost_ratio": 0.45, "elasticity": -1.2},

    # --- Starters & Snacks (6 items) ---
    1878: {"name": "Grilled Tofu Satay with Peanut Dip", "calories": 230, "rating": 4.4, "cost_ratio": 0.44, "elasticity": -1.0},
    2577: {"name": "Crispy Thai Veg Croquettes", "calories": 280, "rating": 4.2, "cost_ratio": 0.42, "elasticity": -1.1},
    2640: {"name": "Golden Spicy Sweet Corn Fritters", "calories": 310, "rating": 4.5, "cost_ratio": 0.40, "elasticity": -1.0},
    1525: {"name": "Crispy Sesame Tofu Bites", "calories": 290, "rating": 4.4, "cost_ratio": 0.43, "elasticity": -1.1},
    2704: {"name": "Crispy Veggie Wontons (6 pcs)", "calories": 270, "rating": 4.5, "cost_ratio": 0.42, "elasticity": -1.0},
    2760: {"name": "Crispy Lotus Stem in Chili Garlic", "calories": 250, "rating": 4.3, "cost_ratio": 0.44, "elasticity": -1.1},

    # --- Soups (3 items) ---
    1438: {"name": "Tom Kha Creamy Coconut Soup", "calories": 190, "rating": 4.3, "cost_ratio": 0.42, "elasticity": -1.0},
    1847: {"name": "Tom Yum Spicy Lemongrass Soup", "calories": 130, "rating": 4.2, "cost_ratio": 0.40, "elasticity": -1.0},
    2494: {"name": "Sweet Corn & Pepper Noodle Soup", "calories": 160, "rating": 4.4, "cost_ratio": 0.41, "elasticity": -0.9},

    # --- Desserts (3 items) ---
    1543: {"name": "Royal Rabri Malpua Cup", "calories": 380, "rating": 4.6, "cost_ratio": 0.46, "elasticity": -1.1},
    2304: {"name": "Kesar Pista Chilled Rasmalai", "calories": 290, "rating": 4.7, "cost_ratio": 0.45, "elasticity": -1.0},
    2492: {"name": "Warm Gulab Jamun Sundae", "calories": 340, "rating": 4.6, "cost_ratio": 0.42, "elasticity": -1.0},

    # --- Extras (3 items) ---
    1198: {"name": "Peri Peri Curly Fries", "calories": 310, "rating": 4.6, "cost_ratio": 0.38, "elasticity": -1.2},
    1311: {"name": "Steamed Veg Dim Sum (4 pcs)", "calories": 220, "rating": 4.5, "cost_ratio": 0.42, "elasticity": -1.0},
    1803: {"name": "Crispy Spring Rolls with Sweet Chili", "calories": 260, "rating": 4.6, "cost_ratio": 0.40, "elasticity": -1.1},

    # --- Fish & Seafood (6 items) ---
    1571: {"name": "Crispy Herb Fish Goujons", "calories": 430, "rating": 4.3, "cost_ratio": 0.52, "elasticity": -1.3},
    2104: {"name": "Pan-Seared Fish Fillet in Garlic Butter", "calories": 410, "rating": 4.4, "cost_ratio": 0.54, "elasticity": -1.2},
    2956: {"name": "Grilled Lemon Pepper Fish Steak", "calories": 380, "rating": 4.5, "cost_ratio": 0.53, "elasticity": -1.2},
    1445: {"name": "Continental Seafood Paella Portion", "calories": 540, "rating": 4.5, "cost_ratio": 0.55, "elasticity": -1.3},
    2444: {"name": "Crispy Panko Fish & Tartar Combo", "calories": 490, "rating": 4.4, "cost_ratio": 0.52, "elasticity": -1.2},
    2867: {"name": "Golden Garlic Herb Prawn Skewers", "calories": 360, "rating": 4.6, "cost_ratio": 0.56, "elasticity": -1.3},
}


class MenuMapper:
    """Maps Kaggle meals to synthetic college canteen items and produces catalogs."""

    def __init__(self, price_scale: float = 1.0):
        self.price_scale = price_scale

    def build_catalogs(
        self,
        historical_df: pd.DataFrame,
        meal_df: pd.DataFrame,
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Build synthetic menu catalog and source mapping DataFrames.

        Args:
            historical_df: Historical orders and price records from train.csv.
            meal_df: Raw meal metadata dataframe.

        Returns:
            Tuple of (catalog_df, mapping_df).
        """
        # Calculate historical price and demand stats per meal
        stats = (
            historical_df.groupby("meal_id")
            .agg(
                hist_mean_checkout=("checkout_price", "mean"),
                hist_mean_base=("base_price", "mean"),
                hist_mean_orders=("num_orders", "mean"),
                hist_total_orders=("num_orders", "sum"),
            )
            .reset_index()
        )

        merged = meal_df.merge(stats, on="meal_id", how="left")
        
        # Sort stably by category, cuisine, meal_id
        merged = merged.sort_values(by=["category", "cuisine", "meal_id"]).reset_index(drop=True)

        catalog_rows = []
        mapping_rows = []

        # Determine popularity tiers based on historical volume quantiles
        median_orders = merged["hist_mean_orders"].median()
        q75_orders = merged["hist_mean_orders"].quantile(0.75)

        for idx, row in merged.iterrows():
            meal_id = int(row["meal_id"])
            item_id = f"MM-{meal_id:04d}"
            category = str(row["category"])
            cuisine = str(row["cuisine"])

            meta = SYNTHETIC_DISH_CATALOG.get(meal_id, {})
            item_name = meta.get("name", f"Synthetic {cuisine} {category} Spec #{meal_id}")
            calories = meta.get("calories", 400)
            base_rating = meta.get("rating", 4.3)
            cost_ratio = meta.get("cost_ratio", 0.45)
            elasticity = meta.get("elasticity", -1.0)

            # Selling price derived from historical checkout price, rounded to whole or .50
            hist_checkout = float(row["hist_mean_checkout"]) if pd.notnull(row["hist_mean_checkout"]) else 250.0
            hist_base = float(row["hist_mean_base"]) if pd.notnull(row["hist_mean_base"]) else 260.0
            hist_orders = float(row["hist_mean_orders"]) if pd.notnull(row["hist_mean_orders"]) else 100.0

            selling_price = round(hist_checkout * self.price_scale, 2)
            prep_cost = round(selling_price * cost_ratio, 2)
            margin = round(selling_price - prep_cost, 2)
            margin_pct = round((margin / selling_price) * 100.0, 1)

            if hist_orders >= q75_orders:
                pop_tier = "High"
            elif hist_orders >= median_orders:
                pop_tier = "Medium"
            else:
                pop_tier = "Low"

            catalog_rows.append({
                "item_id": item_id,
                "item_name": item_name,
                "original_meal_id": meal_id,
                "category": category,
                "cuisine": cuisine,
                "selling_price": selling_price,
                "cost": prep_cost,
                "margin": margin,
                "margin_pct": margin_pct,
                "calories": calories,
                "base_rating": base_rating,
                "popularity_tier": pop_tier,
                "price_elasticity": elasticity,
                "is_synthetic": True,
            })

            mapping_rows.append({
                "original_meal_id": meal_id,
                "original_category": category,
                "original_cuisine": cuisine,
                "synthetic_item_id": item_id,
                "synthetic_item_name": item_name,
                "historical_mean_weekly_orders": round(hist_orders, 1),
                "historical_mean_checkout_price": round(hist_checkout, 2),
                "historical_mean_base_price": round(hist_base, 2),
                "synthetic_selling_price": selling_price,
                "synthetic_cost": prep_cost,
                "synthetic_calories": calories,
                "mapping_notes": f"Synthetic college canteen item mapped from Kaggle meal {meal_id} ({category}/{cuisine})",
            })

        catalog_df = pd.DataFrame(catalog_rows)
        mapping_df = pd.DataFrame(mapping_rows)

        return catalog_df, mapping_df
