"""Automated validation suite for MenuMind synthetic canteen datasets."""

from typing import Dict, Any, List, Tuple
import pandas as pd
import numpy as np


class SyntheticDataValidator:
    """Performs rigorous automated validation on generated synthetic canteen datasets."""

    REQUIRED_DAILY_COLS = [
        "date",
        "item_id",
        "item_name",
        "original_meal_id",
        "category",
        "cuisine",
        "selling_price",
        "cost",
        "calories",
        "qty_prepared",
        "qty_sold",
        "qty_wasted",
        "rating",
        "promotion",
        "day_of_week",
        "is_holiday",
        "demand_estimate",
        "stockout_flag",
    ]

    REQUIRED_CATALOG_COLS = [
        "item_id",
        "item_name",
        "original_meal_id",
        "category",
        "cuisine",
        "selling_price",
        "cost",
        "calories",
        "base_rating",
    ]

    def __init__(self, waste_disposal_cost: float = 2.0):
        self.waste_disposal_cost = waste_disposal_cost

    def run_all_checks(
        self,
        daily_df: pd.DataFrame,
        weekly_df: pd.DataFrame,
        catalog_df: pd.DataFrame,
        mapping_df: pd.DataFrame,
        disaggregation_audit: List[Dict[str, Any]] = None,
    ) -> Tuple[bool, Dict[str, Any]]:
        """Execute complete battery of validation tests.

        Returns:
            Tuple of (all_passed: bool, detailed_results: Dict).
        """
        results: Dict[str, Any] = {}
        all_passed = True

        # 1. Catalog & Mapping Validation
        cat_pass, cat_msgs = self.validate_catalog_and_mapping(catalog_df, mapping_df)
        results["catalog_and_mapping"] = {"passed": cat_pass, "details": cat_msgs}
        if not cat_pass:
            all_passed = False

        # 2. Daily Dataset Schema & Nulls
        schema_pass, schema_msgs = self.validate_schema_and_nulls(daily_df)
        results["schema_and_nulls"] = {"passed": schema_pass, "details": schema_msgs}
        if not schema_pass:
            all_passed = False

        # 3. Duplicate Records
        dup_pass, dup_msgs = self.validate_duplicates(daily_df)
        results["duplicate_check"] = {"passed": dup_pass, "details": dup_msgs}
        if not dup_pass:
            all_passed = False

        # 4. Numerical Ranges & Types
        range_pass, range_msgs = self.validate_numerical_ranges(daily_df)
        results["numerical_ranges"] = {"passed": range_pass, "details": range_msgs}
        if not range_pass:
            all_passed = False

        # 5. Core Accounting Identities
        acc_pass, acc_msgs = self.validate_accounting_identities(daily_df)
        results["accounting_identities"] = {"passed": acc_pass, "details": acc_msgs}
        if not acc_pass:
            all_passed = False

        # 6. Demand Distribution Sanity
        dist_pass, dist_msgs = self.validate_demand_distributions(daily_df)
        results["demand_distribution"] = {"passed": dist_pass, "details": dist_msgs}
        if not dist_pass:
            all_passed = False

        # 7. Daily-to-Weekly Aggregation Consistency
        agg_pass, agg_msgs = self.validate_daily_to_weekly_aggregation(daily_df, weekly_df)
        results["daily_weekly_consistency"] = {"passed": agg_pass, "details": agg_msgs}
        if not agg_pass:
            all_passed = False

        # 8. Weekly Disaggregation Preservation Audit
        if disaggregation_audit:
            pres_pass, pres_msgs = self.validate_disaggregation_preservation(disaggregation_audit)
            results["disaggregation_preservation"] = {"passed": pres_pass, "details": pres_msgs}
            if not pres_pass:
                all_passed = False

        results["summary"] = {
            "overall_status": "PASSED" if all_passed else "FAILED",
            "daily_records_count": len(daily_df),
            "weekly_records_count": len(weekly_df),
            "unique_items_count": int(daily_df["item_id"].nunique()),
            "date_range_start": str(daily_df["date"].min()),
            "date_range_end": str(daily_df["date"].max()),
            "total_prepared_portions": int(daily_df["qty_prepared"].sum()),
            "total_sold_portions": int(daily_df["qty_sold"].sum()),
            "total_wasted_portions": int(daily_df["qty_wasted"].sum()),
            "waste_rate_percentage": round(
                (daily_df["qty_wasted"].sum() / daily_df["qty_prepared"].sum()) * 100.0, 2
            ),
            "stockout_rate_percentage": round(
                (daily_df["stockout_flag"].sum() / len(daily_df)) * 100.0, 2
            ),
            "total_gross_revenue": round(float(daily_df["revenue"].sum()), 2),
            "total_net_profit": round(float(daily_df["profit"].sum()), 2),
        }

        return all_passed, results

    def validate_catalog_and_mapping(
        self, catalog_df: pd.DataFrame, mapping_df: pd.DataFrame
    ) -> Tuple[bool, List[str]]:
        messages = []
        passed = True

        for col in self.REQUIRED_CATALOG_COLS:
            if col not in catalog_df.columns:
                messages.append(f"Missing required catalog column: {col}")
                passed = False

        if catalog_df["item_id"].duplicated().any():
            messages.append("Duplicate item_id detected in menu catalog.")
            passed = False

        if catalog_df["original_meal_id"].duplicated().any():
            messages.append("Duplicate original_meal_id detected in menu catalog.")
            passed = False

        if (catalog_df["selling_price"] <= 0).any():
            messages.append("Non-positive selling price found in catalog.")
            passed = False

        if (catalog_df["cost"] <= 0).any():
            messages.append("Non-positive preparation cost found in catalog.")
            passed = False

        if (catalog_df["selling_price"] < catalog_df["cost"]).any():
            messages.append("Selling price below unit cost detected (negative margin).")
            passed = False

        if not set(mapping_df["synthetic_item_id"]).issubset(set(catalog_df["item_id"])):
            messages.append("Broken mapping: some synthetic_item_ids in mapping not found in catalog.")
            passed = False

        if not messages:
            messages.append("Catalog and mapping passed: all items unique, prices positive, margins healthy.")

        return passed, messages

    def validate_schema_and_nulls(self, daily_df: pd.DataFrame) -> Tuple[bool, List[str]]:
        messages = []
        passed = True

        missing_cols = [c for c in self.REQUIRED_DAILY_COLS if c not in daily_df.columns]
        if missing_cols:
            messages.append(f"Missing required daily columns: {missing_cols}")
            passed = False

        null_counts = daily_df[self.REQUIRED_DAILY_COLS].isnull().sum()
        cols_with_nulls = null_counts[null_counts > 0]
        if not cols_with_nulls.empty:
            messages.append(f"Null values detected in columns: {cols_with_nulls.to_dict()}")
            passed = False

        if not messages:
            messages.append(f"Schema and completeness verified: all {len(self.REQUIRED_DAILY_COLS)} required columns present with 0 nulls.")

        return passed, messages

    def validate_duplicates(self, daily_df: pd.DataFrame) -> Tuple[bool, List[str]]:
        messages = []
        passed = True

        dup_count = daily_df.duplicated(subset=["date", "item_id"]).sum()
        if dup_count > 0:
            messages.append(f"Duplicate (date, item_id) pairs found: {dup_count} records.")
            passed = False
        else:
            messages.append("No duplicate (date, item_id) records found.")

        return passed, messages

    def validate_numerical_ranges(self, daily_df: pd.DataFrame) -> Tuple[bool, List[str]]:
        messages = []
        passed = True

        # Non-negative quantities
        for q_col in ["qty_prepared", "qty_sold", "qty_wasted", "demand_estimate"]:
            if (daily_df[q_col] < 0).any():
                messages.append(f"Negative values found in {q_col}.")
                passed = False

        # Positive prices and costs
        if (daily_df["selling_price"] <= 0).any():
            messages.append("Non-positive values found in selling_price.")
            passed = False

        if (daily_df["cost"] <= 0).any():
            messages.append("Non-positive values found in cost.")
            passed = False

        # Ratings 1 to 5
        if ((daily_df["rating"] < 1.0) | (daily_df["rating"] > 5.0)).any():
            messages.append("Rating values out of [1.0, 5.0] range detected.")
            passed = False

        # Flags binary 0 or 1
        for flag_col in ["promotion", "is_holiday", "stockout_flag"]:
            invalid = ~daily_df[flag_col].isin([0, 1])
            if invalid.any():
                messages.append(f"Invalid non-binary flag values in {flag_col}.")
                passed = False

        if not messages:
            messages.append("Numerical ranges valid: all quantities >= 0, prices > 0, ratings within [1, 5].")

        return passed, messages

    def validate_accounting_identities(self, daily_df: pd.DataFrame) -> Tuple[bool, List[str]]:
        messages = []
        passed = True

        # Check 1: qty_sold == min(demand_estimate, qty_prepared)
        expected_sold = np.minimum(daily_df["demand_estimate"], daily_df["qty_prepared"])
        sold_mismatch = (daily_df["qty_sold"] != expected_sold).sum()
        if sold_mismatch > 0:
            messages.append(f"qty_sold violation: {sold_mismatch} rows fail qty_sold == min(demand, prepared)")
            passed = False

        # Check 2: qty_wasted == max(0, qty_prepared - qty_sold)
        expected_waste = np.maximum(0, daily_df["qty_prepared"] - daily_df["qty_sold"])
        waste_mismatch = (daily_df["qty_wasted"] != expected_waste).sum()
        if waste_mismatch > 0:
            messages.append(f"qty_wasted violation: {waste_mismatch} rows fail qty_wasted == max(0, prepared - sold)")
            passed = False

        # Check 3: stockout_flag == (demand_estimate > qty_prepared)
        expected_stockout = (daily_df["demand_estimate"] > daily_df["qty_prepared"]).astype(int)
        stockout_mismatch = (daily_df["stockout_flag"] != expected_stockout).sum()
        if stockout_mismatch > 0:
            messages.append(f"stockout_flag violation: {stockout_mismatch} rows fail stockout_flag == (demand > prepared)")
            passed = False

        # Check 4: Conservation of mass: qty_sold + qty_wasted == qty_prepared
        mass_mismatch = (daily_df["qty_sold"] + daily_df["qty_wasted"] != daily_df["qty_prepared"]).sum()
        if mass_mismatch > 0:
            messages.append(f"Conservation violation: {mass_mismatch} rows fail qty_sold + qty_wasted == qty_prepared")
            passed = False

        # Check 5: Revenue identity: revenue == round(qty_sold * selling_price, 2)
        expected_rev = np.round(daily_df["qty_sold"] * daily_df["selling_price"], 2)
        rev_mismatch = (np.abs(daily_df["revenue"] - expected_rev) > 0.02).sum()
        if rev_mismatch > 0:
            messages.append(f"revenue violation: {rev_mismatch} rows fail revenue == qty_sold * selling_price")
            passed = False

        # Check 6: Preparation cost identity: preparation_cost == round(qty_prepared * cost, 2)
        expected_cost = np.round(daily_df["qty_prepared"] * daily_df["cost"], 2)
        cost_mismatch = (np.abs(daily_df["preparation_cost"] - expected_cost) > 0.02).sum()
        if cost_mismatch > 0:
            messages.append(f"preparation_cost violation: {cost_mismatch} rows fail preparation_cost == qty_prepared * cost")
            passed = False

        # Check 7: Profit identity: profit == round(revenue - preparation_cost - qty_wasted * disposal_cost, 2)
        expected_profit = np.round(
            daily_df["revenue"] - daily_df["preparation_cost"] - (daily_df["qty_wasted"] * self.waste_disposal_cost),
            2,
        )
        profit_mismatch = (np.abs(daily_df["profit"] - expected_profit) > 0.05).sum()
        if profit_mismatch > 0:
            messages.append(f"profit violation: {profit_mismatch} rows fail profit identity")
            passed = False

        if not messages:
            messages.append("All 7 accounting identities strictly satisfied across 100% of rows.")

        return passed, messages

    def validate_demand_distributions(self, daily_df: pd.DataFrame) -> Tuple[bool, List[str]]:
        messages = []
        passed = True

        # Check for zero or negative variance in demand
        demand_std = daily_df["demand_estimate"].std()
        if demand_std < 1.0:
            messages.append(f"Degenerate demand distribution: standard deviation is too low ({demand_std:.2f})")
            passed = False

        # Check that popular categories have higher volume than specialty categories
        cat_avg = daily_df.groupby("category")["qty_sold"].mean()
        if "Rice Bowl" in cat_avg and "Soup" in cat_avg:
            if cat_avg["Rice Bowl"] <= cat_avg["Soup"]:
                messages.append("Suspicious popularity distribution: Soup average sales exceed Rice Bowl.")
                # Warning rather than hard fail

        messages.append(f"Demand distribution healthy: mean daily demand = {daily_df['demand_estimate'].mean():.1f}, std = {demand_std:.1f}.")
        return passed, messages

    def validate_daily_to_weekly_aggregation(
        self, daily_df: pd.DataFrame, weekly_df: pd.DataFrame
    ) -> Tuple[bool, List[str]]:
        messages = []
        passed = True

        # Check total quantities match
        daily_sold = daily_df["qty_sold"].sum()
        weekly_sold = weekly_df["qty_sold"].sum()
        if daily_sold != weekly_sold:
            messages.append(f"Aggregation mismatch: daily sold ({daily_sold}) != weekly sold ({weekly_sold})")
            passed = False

        daily_waste = daily_df["qty_wasted"].sum()
        weekly_waste = weekly_df["qty_wasted"].sum()
        if daily_waste != weekly_waste:
            messages.append(f"Aggregation mismatch: daily waste ({daily_waste}) != weekly waste ({weekly_waste})")
            passed = False

        daily_rev = daily_df["revenue"].sum()
        weekly_rev = weekly_df["revenue"].sum()
        if abs(daily_rev - weekly_rev) > 1.0:
            messages.append(f"Aggregation mismatch: daily revenue ({daily_rev:.2f}) != weekly revenue ({weekly_rev:.2f})")
            passed = False

        if not messages:
            messages.append("Daily-to-weekly aggregation verified: 100% consistent across sold, wasted, and revenue totals.")

        return passed, messages

    def validate_disaggregation_preservation(
        self, audit_records: List[Dict[str, Any]]
    ) -> Tuple[bool, List[str]]:
        messages = []
        passed = True

        failures = 0
        for rec in audit_records:
            if rec["target_weekly_total"] != rec["disaggregated_sum"]:
                failures += 1

        if failures > 0:
            messages.append(f"Disaggregation preservation failed in {failures} item-weeks!")
            passed = False
        else:
            messages.append(f"Weekly total preservation verified: exactly preserved across all {len(audit_records)} item-weeks.")

        return passed, messages
