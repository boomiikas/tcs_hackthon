"""Unit tests for MenuMind synthetic canteen data pipeline and Rewind simulator."""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path

from src.config import MenuMindConfig
from src.data_loader import RawDataLoader
from src.menu_mapper import MenuMapper, SYNTHETIC_DISH_CATALOG
from src.academic_calendar import AcademicCalendar
from src.disaggregator import DemandDisaggregator
from src.kitchen_policy import KitchenSimulator
from src.rewind_engine import MenuMindRewindSimulator
from src.validator import SyntheticDataValidator


def test_disaggregator_exact_preservation():
    """Verify that integer disaggregation strictly preserves weekly totals."""
    disaggregator = DemandDisaggregator(demand_scale=0.15, random_seed=42)

    test_totals = [0, 1, 7, 10, 43, 100, 255, 1000]
    categories = ["Beverages", "Pizza", "Rice Bowl", "Salad", "Biryani"]

    for tot in test_totals:
        for cat in categories:
            shares = disaggregator.disaggregate_weekly_total(tot, cat)
            assert len(shares) == 7
            assert np.all(shares >= 0)
            assert int(np.sum(shares)) == tot, f"Failed preservation for total {tot} in {cat}"


def test_accounting_identities_exhaustive():
    """Verify operational accounting identities across extreme scenarios."""
    kitchen = KitchenSimulator(waste_disposal_cost=2.0)

    test_cases = [
        # (demand, prep, price, cost)
        (50, 50, 100.0, 45.0),   # exact match
        (60, 40, 120.0, 50.0),   # under-prepared (stockout)
        (30, 50, 80.0, 35.0),    # over-prepared (waste)
        (0, 20, 150.0, 60.0),    # zero demand (100% waste)
        (25, 0, 90.0, 40.0),     # zero prep (100% stockout)
        (0, 0, 100.0, 50.0),     # zero everything
    ]

    for d, q, p, c in test_cases:
        acc = kitchen.execute_daily_accounting(d, q, p, c)
        assert acc["qty_sold"] == min(d, q)
        assert acc["qty_wasted"] == max(0, q - acc["qty_sold"])
        assert acc["qty_sold"] + acc["qty_wasted"] == q
        assert acc["stockout_flag"] == int(d > q)
        assert acc["missed_demand"] == max(0, d - q)
        assert acc["revenue"] == round(acc["qty_sold"] * p, 2)
        assert acc["preparation_cost"] == round(q * c, 2)
        expected_profit = round(acc["revenue"] - acc["preparation_cost"] - (acc["qty_wasted"] * 2.0), 2)
        assert acc["profit"] == expected_profit


def test_menu_catalog_and_mapping():
    """Verify catalog has all 51 meals mapped with positive margins and valid calories."""
    assert len(SYNTHETIC_DISH_CATALOG) == 51

    # Fake mini historical dataframe
    hist_df = pd.DataFrame([
        {"meal_id": mid, "checkout_price": 200.0, "base_price": 220.0, "num_orders": 150}
        for mid in SYNTHETIC_DISH_CATALOG
    ])
    meal_df = pd.DataFrame([
        {"meal_id": mid, "category": "Beverages", "cuisine": "Thai"}
        for mid in SYNTHETIC_DISH_CATALOG
    ])

    mapper = MenuMapper(price_scale=1.0)
    catalog_df, mapping_df = mapper.build_catalogs(hist_df, meal_df)

    assert len(catalog_df) == 51
    assert len(mapping_df) == 51
    assert catalog_df["item_id"].nunique() == 51
    assert (catalog_df["selling_price"] > catalog_df["cost"]).all()
    assert (catalog_df["calories"] > 0).all()
    assert ((catalog_df["base_rating"] >= 1.0) & (catalog_df["base_rating"] <= 5.0)).all()


def test_academic_calendar_coverage():
    """Verify academic calendar generates 364 days for 52 weeks with valid events."""
    calendar = AcademicCalendar(start_date="2025-01-06", num_weeks=52)
    df = calendar.generate_calendar_days()

    assert len(df) == 364
    assert df["week_number"].nunique() == 52
    assert "Annual Cultural Fest" in df["campus_event"].values
    assert "Midterm Exam Week" in df["campus_event"].values
    assert "Summer Vacation Break" in df["campus_event"].values
    assert df["is_holiday"].isin([0, 1]).all()


def test_rewind_simulator_regrets():
    """Verify MenuMind Rewind regret equations and counterfactual simulation."""
    sim = MenuMindRewindSimulator(waste_disposal_cost=2.0)

    # Over-preparation scenario: Demand 40, Prepared 60
    # Price 100, Cost 40, Disposal 2
    res_over = sim.evaluate_decision(demand=40, prepared=60, selling_price=100.0, unit_cost=40.0)
    assert res_over["portions_sold"] == 40
    assert res_over["leftover_portions"] == 20
    assert res_over["missed_demand"] == 0
    # Revenue = 4000, Cost = 2400, Disp = 40 -> Net Profit = 1560
    assert res_over["estimated_profit"] == 1560.0
    # Optimal Profit = 40 * (100 - 40) = 2400
    assert res_over["optimal_profit"] == 2400.0
    # Profit Regret = 2400 - 1560 = 840
    assert res_over["profit_regret"] == 840.0
    # Waste Regret = 20 * (40 + 2) = 840
    assert res_over["waste_regret"] == 840.0
    assert res_over["missed_demand_regret"] == 0.0

    # Under-preparation scenario: Demand 60, Prepared 40
    res_under = sim.evaluate_decision(demand=60, prepared=40, selling_price=100.0, unit_cost=40.0)
    assert res_under["portions_sold"] == 40
    assert res_under["leftover_portions"] == 0
    assert res_under["missed_demand"] == 20
    # Revenue = 4000, Cost = 1600 -> Net Profit = 2400
    assert res_under["estimated_profit"] == 2400.0
    # Optimal Profit = 60 * 60 = 3600
    assert res_under["optimal_profit"] == 3600.0
    # Missed Demand Regret = 20 * (100 - 40) = 1200
    assert res_under["missed_demand_regret"] == 1200.0
    assert res_under["profit_regret"] == 1200.0
    assert res_under["waste_regret"] == 0.0
