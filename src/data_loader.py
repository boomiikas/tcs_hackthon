"""Source data loader and validation for Kaggle Food Demand Forecasting files."""

import os
from pathlib import Path
from typing import Tuple, Dict, Any
import pandas as pd
import numpy as np


class RawDataLoader:
    """Safely loads, merges, and validates the Kaggle food demand forecasting source data."""

    REQUIRED_FILES = [
        "meal_info.csv",
        "fulfilment_center_info.csv",
        "train.csv",
    ]

    def __init__(self, raw_dir: str = "data/raw"):
        self.raw_dir = Path(raw_dir)

    def verify_files_exist(self) -> None:
        """Verify that required source CSV files exist, or raise an actionable error."""
        missing = [f for f in self.REQUIRED_FILES if not (self.raw_dir / f).exists()]
        if missing:
            raise FileNotFoundError(
                f"\n[MenuMind Data Error] Missing required source files in '{self.raw_dir}': {missing}\n"
                "Please download the dataset from Kaggle:\n"
                "  https://www.kaggle.com/datasets/kannanaikkal/food-demand-forecasting\n"
                f"and extract the following CSV files into '{self.raw_dir}/':\n"
                "  - train.csv\n"
                "  - meal_info.csv\n"
                "  - fulfilment_center_info.csv\n"
                "  - test.csv (optional)\n"
            )

    def load_and_merge(
        self,
        center_id: int = 13,
        num_weeks: int = 52,
        start_week: int = 1,
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
        """Load source files, merge demand with meal and center metadata, and validate keys.

        Args:
            center_id: Fulfillment center ID to extract historical demand from (default 13).
            num_weeks: Number of weeks to extract.
            start_week: Starting week number in source data.

        Returns:
            Tuple of:
              - merged_center_df: historical demand for the target center
              - meal_info_df: full meal metadata
              - center_info_df: full center metadata
              - audit_info: validation audit dictionary
        """
        self.verify_files_exist()

        meal_path = self.raw_dir / "meal_info.csv"
        center_path = self.raw_dir / "fulfilment_center_info.csv"
        train_path = self.raw_dir / "train.csv"

        meal_df = pd.read_csv(meal_path)
        center_df = pd.read_csv(center_path)
        train_df = pd.read_csv(train_path)

        # Audit raw records
        raw_rows = len(train_df)
        raw_meals = len(meal_df)
        raw_centers = len(center_df)

        # Integrity check: missing values in raw keys
        if train_df[["meal_id", "center_id", "week", "num_orders"]].isnull().any().any():
            raise ValueError("Raw train.csv contains null values in key columns!")

        # Perform left joins
        merged = train_df.merge(meal_df, on="meal_id", how="left")
        if merged["category"].isnull().any():
            unmatched = merged[merged["category"].isnull()]["meal_id"].unique()
            raise ValueError(f"Unmatched meal_ids found in train data: {unmatched}")

        merged = merged.merge(center_df, on="center_id", how="left")
        if merged["center_type"].isnull().any():
            unmatched_c = merged[merged["center_type"].isnull()]["center_id"].unique()
            raise ValueError(f"Unmatched center_ids found in train data: {unmatched_c}")

        # Check for duplicates on (week, center_id, meal_id)
        dup_count = merged.duplicated(subset=["week", "center_id", "meal_id"]).sum()
        if dup_count > 0:
            # deduplicate if any duplicates exist in raw data
            merged = merged.drop_duplicates(subset=["week", "center_id", "meal_id"])

        # Filter for requested center_id
        if center_id not in merged["center_id"].values:
            available_centers = merged["center_id"].unique()
            raise ValueError(
                f"Center ID {center_id} not found in train data. Available: {available_centers[:10]}..."
            )

        center_data = merged[merged["center_id"] == center_id].copy()

        # Filter week range
        end_week = start_week + num_weeks - 1
        max_source_week = center_data["week"].max()
        if end_week > max_source_week:
            end_week = max_source_week
        
        filtered_center_data = center_data[
            (center_data["week"] >= start_week) & (center_data["week"] <= end_week)
        ].copy()

        # Sort cleanly
        filtered_center_data = filtered_center_data.sort_values(by=["week", "meal_id"]).reset_index(drop=True)

        audit_info = {
            "raw_train_rows": raw_rows,
            "raw_meals_count": raw_meals,
            "raw_centers_count": raw_centers,
            "center_id": center_id,
            "center_type": center_df.loc[center_df["center_id"] == center_id, "center_type"].values[0],
            "op_area": float(center_df.loc[center_df["center_id"] == center_id, "op_area"].values[0]),
            "extracted_weeks": int(filtered_center_data["week"].nunique()),
            "start_week": int(filtered_center_data["week"].min()),
            "end_week": int(filtered_center_data["week"].max()),
            "extracted_rows": len(filtered_center_data),
            "unique_meals_at_center": int(filtered_center_data["meal_id"].nunique()),
            "total_raw_orders": int(filtered_center_data["num_orders"].sum()),
        }

        return filtered_center_data, meal_df, center_df, audit_info
