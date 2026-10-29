"""Data loading and schema validation pipeline for CanteenIQ."""

import os
from pathlib import Path
from typing import Tuple, Dict, Any, Optional
import pandas as pd
import numpy as np


class CanteenDataLoader:
    """Robust data loader that discovers, validates, and normalizes canteen operational datasets."""

    DEFAULT_PATHS = [
        "data/processed/synthetic_canteen_daily.csv",
        "data/synthetic_canteen_daily.csv",
        "data/processed/synthetic_canteen_weekly.csv",
    ]

    REQUIRED_COLUMNS = [
        "date",
        "item_name",
        "category",
        "price",
        "cost",
        "calories",
        "qty_prepared",
        "qty_sold",
        "qty_wasted",
        "rating",
    ]

    def __init__(self, filepath: Optional[str] = None):
        self.filepath = self._resolve_filepath(filepath)

    def _resolve_filepath(self, filepath: Optional[str]) -> Path:
        """Find the dataset file or search standard locations."""
        if filepath and Path(filepath).exists():
            return Path(filepath)

        for p in self.DEFAULT_PATHS:
            if Path(p).exists():
                return Path(p)

        raise FileNotFoundError(
            f"[CanteenIQ Data Error] Dataset file could not be found.\n"
            f"Searched locations: {self.DEFAULT_PATHS}\n"
            "Please provide a valid filepath or ensure 'data/processed/synthetic_canteen_daily.csv' exists."
        )

    def load_and_validate(self) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Load the dataset, normalize column aliases, and run validation checks.

        Returns:
            Tuple of (clean_df, audit_report_dict)
        """
        raw_df = pd.read_csv(self.filepath)
        initial_rows = len(raw_df)

        # Normalize column aliases
        df = raw_df.copy()
        if "selling_price" in df.columns and "price" not in df.columns:
            df["price"] = df["selling_price"]

        # Verify required columns
        missing_cols = [c for c in self.REQUIRED_COLUMNS if c not in df.columns]
        if missing_cols:
            raise ValueError(
                f"[CanteenIQ Schema Error] Dataset '{self.filepath}' is missing required columns: {missing_cols}"
            )

        # Parse date
        df["date"] = pd.to_datetime(df["date"])

        # Check and handle duplicates on (date, item_name)
        dup_mask = df.duplicated(subset=["date", "item_name"], keep="first")
        duplicates_removed = int(dup_mask.sum())
        if duplicates_removed > 0:
            df = df[~dup_mask].copy()

        # Validate numerical ranges
        # Filter non-negative quantities and positive financial metrics
        valid_mask = (
            (df["price"] > 0)
            & (df["cost"] > 0)
            & (df["calories"] > 0)
            & (df["qty_prepared"] >= 0)
            & (df["qty_sold"] >= 0)
            & (df["qty_wasted"] >= 0)
            & (df["rating"] >= 1.0)
            & (df["rating"] <= 5.0)
        )
        invalid_rows = int((~valid_mask).sum())
        if invalid_rows > 0:
            df = df[valid_mask].copy()

        # Sort chronologically strictly by date, then item_name
        df = df.sort_values(by=["date", "item_name"]).reset_index(drop=True)

        audit_report = {
            "dataset_filepath": str(self.filepath.resolve()),
            "initial_rows": initial_rows,
            "final_clean_rows": len(df),
            "duplicates_removed": duplicates_removed,
            "invalid_rows_removed": invalid_rows,
            "start_date": df["date"].min().strftime("%Y-%m-%d"),
            "end_date": df["date"].max().strftime("%Y-%m-%d"),
            "total_days": int(df["date"].nunique()),
            "unique_items": int(df["item_name"].nunique()),
            "unique_categories": int(df["category"].nunique()),
            "total_portions_sold": int(df["qty_sold"].sum()),
            "total_portions_wasted": int(df["qty_wasted"].sum()),
            "total_portions_prepared": int(df["qty_prepared"].sum()),
            "average_waste_rate_pct": round(
                (df["qty_wasted"].sum() / df["qty_prepared"].sum() * 100.0), 2
            ),
        }

        return df, audit_report


def load_and_validate_data(filepath: Optional[str] = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Convenience functional interface for loading canteen data."""
    loader = CanteenDataLoader(filepath=filepath)
    return loader.load_and_validate()
