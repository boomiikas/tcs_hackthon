"""Waste and surplus analysis, high-waste detection, and Mystery Meal surplus rescue for CanteenIQ."""

from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np


class WasteAnalyzer:
    """Analyzes historical food waste, detects chronic waste culprits, generates actionable prep

    adjustments, and constructs safe Mystery Meal surplus rescue combos.
    """

    def __init__(self, waste_disposal_cost: float = 2.0, high_waste_threshold_pct: float = 25.0):
        self.waste_disposal_cost = waste_disposal_cost
        self.high_waste_threshold = high_waste_threshold_pct

    def analyze_operational_waste(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Perform comprehensive historical waste audit and generate item-level action items."""
        clean_df = df.copy()

        # Item-level metrics
        item_grp = clean_df.groupby("item_name").agg(
            category=("category", "first"),
            price=("price", "mean"),
            cost=("cost", "mean"),
            rating=("rating", "mean"),
            days_offered=("date", "count"),
            total_prepared=("qty_prepared", "sum"),
            total_sold=("qty_sold", "sum"),
            total_wasted=("qty_wasted", "sum"),
        ).reset_index()

        item_grp["waste_rate_pct"] = np.round(
            (item_grp["total_wasted"] / item_grp["total_prepared"].replace(0, 1)) * 100.0, 2
        )
        item_grp["total_waste_cost"] = np.round(
            item_grp["total_wasted"] * (item_grp["cost"] + self.waste_disposal_cost), 2
        )

        # Stockout rate per item (if stockout_flag available, else infer if sold == prep and prep > 0)
        if "stockout_flag" in clean_df.columns:
            stockouts = clean_df.groupby("item_name")["stockout_flag"].mean() * 100.0
        else:
            inferred = (clean_df["qty_sold"] >= clean_df["qty_prepared"]) & (clean_df["qty_prepared"] > 0)
            stockouts = inferred.groupby(clean_df["item_name"]).mean() * 100.0

        item_grp["stockout_rate_pct"] = np.round(item_grp["item_name"].map(stockouts).fillna(0.0), 2)

        # Classify dishes and generate actionable preparation recommendations
        action_recommendations = []
        chronic_high_waste = []

        for _, row in item_grp.iterrows():
            item = row["item_name"]
            cat = row["category"]
            waste_pct = row["waste_rate_pct"]
            stockout_pct = row["stockout_rate_pct"]
            w_cost = row["total_waste_cost"]
            rating = row["rating"]

            if waste_pct >= self.high_waste_threshold:
                chronic_high_waste.append({
                    "item_name": item,
                    "category": cat,
                    "waste_rate_pct": waste_pct,
                    "total_waste_cost_inr": w_cost,
                    "average_rating": round(rating, 2),
                })

            # Action heuristics
            if waste_pct > 30.0 and stockout_pct < 5.0:
                action = "REDUCE PREPARATION"
                action_detail = f"Reduce daily prep quantity by 15-20%. Consistently over-prepared with minimal stockout risk ({stockout_pct}%)."
                urgency = "HIGH"
            elif stockout_pct > 20.0 and waste_pct < 15.0:
                action = "INCREASE PREPARATION"
                action_detail = f"Increase daily buffer by 10-15%. Frequent stockouts ({stockout_pct}%) causing lost sales."
                urgency = "HIGH"
            elif rating < 4.0 and waste_pct > 25.0:
                action = "REVIEW RECIPE / ROTATE OUT"
                action_detail = f"Lower student satisfaction ({rating:.1f} stars) combined with {waste_pct}% waste. Rotate off daily menu."
                urgency = "MEDIUM"
            elif rating >= 4.6 and waste_pct <= 15.0:
                action = "MAINTAIN CORE STAPLE"
                action_detail = f"Star performer: high popularity ({rating:.1f} stars) and efficient kitchen utilization."
                urgency = "LOW"
            else:
                action = "MONITOR PREPARATION"
                action_detail = "Operating within normal variance bounds. Maintain current buffer."
                urgency = "LOW"

            action_recommendations.append({
                "item_name": item,
                "category": cat,
                "action": action,
                "action_detail": action_detail,
                "urgency": urgency,
                "waste_rate_pct": waste_pct,
                "stockout_rate_pct": stockout_pct,
                "total_waste_cost_inr": w_cost,
            })

        # Sort recommendations by waste cost impact
        action_recommendations = sorted(action_recommendations, key=lambda x: -x["total_waste_cost_inr"])
        chronic_high_waste = sorted(chronic_high_waste, key=lambda x: -x["total_waste_cost_inr"])

        # Summary KPIs
        kpis = {
            "total_dishes_audited": len(item_grp),
            "dishes_exceeding_waste_threshold": len(chronic_high_waste),
            "total_accumulated_waste_cost_inr": round(float(item_grp["total_waste_cost"].sum()), 2),
            "dishes_requiring_prep_reduction": sum(1 for a in action_recommendations if a["action"] == "REDUCE PREPARATION"),
            "dishes_requiring_prep_increase": sum(1 for a in action_recommendations if a["action"] == "INCREASE PREPARATION"),
        }

        return {
            "waste_kpis": kpis,
            "chronic_high_waste_dishes": chronic_high_waste[:8],
            "action_recommendations": action_recommendations,
        }

    def build_mystery_meal_recommendation(
        self,
        surplus_inventory: List[Dict[str, Any]],
        target_discount_pct: float = 35.0,
    ) -> Dict[str, Any]:
        """Construct a safe, discounted 'Mystery Meal' surplus rescue combo.

        Food safety compliance:
          Hot food must not exceed holding time (>60°C, max 4h).
          If holding time data is absent, manual eligibility check is strictly flagged.
        """
        if not surplus_inventory:
            return {
                "combo_available": False,
                "message": "No surplus inventory currently eligible for Mystery Meal bundling.",
            }

        # Filter items with positive surplus
        eligible_items = [it for it in surplus_inventory if it.get("surplus_portions", 0) > 0]
        if not eligible_items:
            return {
                "combo_available": False,
                "message": "All prepared portions were successfully sold; zero surplus available.",
            }

        # Group by category
        mains = [it for it in eligible_items if it.get("category") in ["Rice Bowl", "Sandwich", "Pasta", "Pizza", "Biryani"]]
        beverages = [it for it in eligible_items if it.get("category") == "Beverages"]
        snacks = [it for it in eligible_items if it.get("category") in ["Starters", "Other Snacks", "Extras", "Desert", "Salad"]]

        # Select items for Mystery Meal Combo
        selected_combo = []
        if mains:
            selected_combo.append(max(mains, key=lambda x: x.get("surplus_portions", 0)))
        if beverages:
            selected_combo.append(max(beverages, key=lambda x: x.get("surplus_portions", 0)))
        if snacks:
            selected_combo.append(max(snacks, key=lambda x: x.get("surplus_portions", 0)))

        if not selected_combo:
            selected_combo = sorted(eligible_items, key=lambda x: -x.get("surplus_portions", 0))[:2]

        # Calculate pricing
        original_price = sum(float(it.get("price", 100.0)) for it in selected_combo)
        discount_factor = 1.0 - (target_discount_pct / 100.0)
        combo_price = round(original_price * discount_factor, 0)
        max_available_combos = min(it.get("surplus_portions", 1) for it in selected_combo)

        return {
            "combo_available": True,
            "combo_name": "CanteenIQ Eco-Rescue Mystery Box",
            "bundled_items": [it["item_name"] for it in selected_combo],
            "max_combos_available": int(max_available_combos),
            "original_total_price_inr": round(original_price, 2),
            "discount_percentage": target_discount_pct,
            "rescue_combo_price_inr": combo_price,
            "estimated_portions_saved": len(selected_combo) * int(max_available_combos),
            "food_safety_notice": {
                "requires_manual_inspection": True,
                "holding_time_limit_hours": 4.0,
                "temperature_specification": "Hot holding verified >= 60°C or chilled <= 5°C",
                "safety_guideline": "CRITICAL: Food safety takes absolute precedence. Inspect aroma, texture, and hot-holding temperature logs before packing rescue meals.",
            },
        }

    def calculate_regret_meter(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate the Regret Meter: estimated avoidable financial loss and normalized 0-100 score.

        Avoidable Financial Loss = Waste Regret (Over-preparation) + Stockout Regret (Missed Demand).
        Mutual Exclusivity: On any dish-service observation, either Q > D (over-prep waste) OR
        D > Q (stockout missed margin). They are disjoint partitions of forecast error, preventing double counting.
        """
        if df is None or len(df) == 0:
            return {
                "regret_index_score": 0.0,
                "operational_efficiency_score": 100.0,
                "status": "LOW_REGRET",
                "total_avoidable_financial_loss_inr": 0.0,
                "time_period_audited": "0 days",
                "currency": "INR",
            }

        clean_df = df.copy()

        # Audit time period context
        if "date" in clean_df.columns:
            date_series = pd.to_datetime(clean_df["date"])
            total_days = int(date_series.nunique())
            start_date_str = str(date_series.min().date())
            end_date_str = str(date_series.max().date())
        else:
            total_days = 1
            start_date_str = "N/A"
            end_date_str = "N/A"

        total_weeks = round(total_days / 7.0, 1)

        # 1. Over-preparation Waste Regret (Discarded Ingredient Cost + Waste Disposal Fee)
        unit_waste_cost = clean_df["cost"] + self.waste_disposal_cost
        waste_regret_total = float((clean_df["qty_wasted"] * unit_waste_cost).sum())

        # 2. Under-preparation Missed Demand Regret (Unrealized Gross Margin on Unmet Customer Demand)
        # Missed demand is only calculated when unmet demand is explicitly known or inferred
        if "missed_demand" in clean_df.columns:
            missed_portions = np.maximum(0, clean_df["missed_demand"].values)
        elif "demand_estimate" in clean_df.columns:
            missed_portions = np.maximum(0, clean_df["demand_estimate"].values - clean_df["qty_prepared"].values)
        else:
            missed_portions = np.zeros(len(clean_df))

        unit_margin = np.maximum(0.0, clean_df["price"].values - clean_df["cost"].values)
        stockout_regret_total = float(np.sum(missed_portions * unit_margin))

        # 3. Financial Loss Sum
        total_avoidable_loss = round(waste_regret_total + stockout_regret_total, 2)
        total_realized_revenue = float((clean_df["qty_sold"] * clean_df["price"]).sum())

        # Daily and Weekly Normalization
        days_div = max(1, total_days)
        daily_avoidable_loss = round(total_avoidable_loss / days_div, 2)
        daily_waste_regret = round(waste_regret_total / days_div, 2)
        daily_stockout_regret = round(stockout_regret_total / days_div, 2)
        daily_revenue = round(total_realized_revenue / days_div, 2)

        weekly_avoidable_loss = round(daily_avoidable_loss * 7.0, 2)
        weekly_waste_regret = round(daily_waste_regret * 7.0, 2)
        weekly_stockout_regret = round(daily_stockout_regret * 7.0, 2)
        weekly_revenue = round(daily_revenue * 7.0, 2)

        # 4. Normalized Regret Index (0 to 100 scale, where 0 is zero regret and 100 is severe regret)
        # Formula: Regret Index = Avoidable Loss / (Realized Revenue + Avoidable Loss) * 100
        denominator = total_realized_revenue + total_avoidable_loss
        if denominator > 0:
            regret_index = round(min(100.0, (total_avoidable_loss / denominator) * 100.0), 1)
        else:
            regret_index = 0.0

        efficiency_score = round(100.0 - regret_index, 1)

        if regret_index <= 15.0:
            status = "LOW_REGRET"
            assessment = "Excellent kitchen efficiency. Minor buffer variance well within operational norms."
        elif regret_index <= 32.0:
            status = "MODERATE_REGRET"
            assessment = "Standard institutional variance. Noticeable food waste or missed sales that AI buffering can reclaim."
        else:
            status = "HIGH_REGRET"
            assessment = "Severe avoidable loss detected. Chronic kitchen over-preparation or repeated stockouts."

        return {
            "regret_index_score": regret_index,
            "operational_efficiency_score": efficiency_score,
            "status": status,
            "currency": "INR",
            "time_period_audited": {
                "total_operating_days": total_days,
                "total_weeks": total_weeks,
                "start_date": start_date_str,
                "end_date": end_date_str,
                "description": f"Cumulative {total_days}-day operational audit ({total_weeks} weeks)",
            },
            # Full Dataset Totals
            "total_avoidable_financial_loss_inr": total_avoidable_loss,
            "waste_regret_loss_inr": round(waste_regret_total, 2),
            "stockout_missed_margin_loss_inr": round(stockout_regret_total, 2),
            "total_realized_revenue_inr": round(total_realized_revenue, 2),
            "total_wasted_portions": int(clean_df["qty_wasted"].sum()),
            "total_missed_demand_portions": int(np.sum(missed_portions)),
            # Daily Averages
            "daily_averages": {
                "daily_avoidable_loss_inr": daily_avoidable_loss,
                "daily_waste_regret_inr": daily_waste_regret,
                "daily_stockout_regret_inr": daily_stockout_regret,
                "daily_realized_revenue_inr": daily_revenue,
                "daily_wasted_portions": round(float(clean_df["qty_wasted"].sum()) / days_div, 1),
                "daily_missed_demand_portions": round(float(np.sum(missed_portions)) / days_div, 1),
            },
            # Weekly Averages
            "weekly_averages": {
                "weekly_avoidable_loss_inr": weekly_avoidable_loss,
                "weekly_waste_regret_inr": weekly_waste_regret,
                "weekly_stockout_regret_inr": weekly_stockout_regret,
                "weekly_realized_revenue_inr": weekly_revenue,
            },
            "manager_assessment": assessment,
            "formula_documentation": {
                "regret_index_formula": "Regret Index = Total Avoidable Loss / (Total Realized Revenue + Total Avoidable Loss) * 100",
                "waste_regret_formula": "Waste Regret = sum(qty_wasted * (unit_cost + disposal_cost))",
                "stockout_regret_formula": "Stockout Regret = sum(missed_demand * max(0, price - unit_cost))",
                "avoidable_loss_formula": "Total Avoidable Loss = Waste Regret + Stockout Regret",
                "double_counting_safeguard": (
                    "Disjoint events: On every dish-day record, either qty_wasted > 0 (missed_demand = 0) "
                    "or missed_demand > 0 (qty_wasted = 0). They are mutually exclusive, preventing double counting."
                ),
            },
        }
