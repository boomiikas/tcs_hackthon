"""Feature engineering and temporal data preparation pipeline for CanteenIQ demand forecasting."""

from typing import Tuple, List, Dict, Any, Optional
import pandas as pd
import numpy as np


class CanteenFeatureEngineer:
    """Extracts date, lag, and rolling features while strictly preventing temporal data leakage.

    Guarantees:
      - All sales lags and rolling statistics use historical data prior to prediction date (shift >= 1).
      - Same-day actual sales, waste, and preparation quantities are strictly excluded from feature inputs.
      - Splitting is performed chronologically.
    """

    CATEGORICAL_COLS = ["category"]
    NUMERICAL_COLS = [
        "price",
        "cost",
        "margin",
        "margin_pct",
        "calories",
        "rating",
        "day_of_week",
        "is_weekend",
        "month",
        "day_of_month",
        "sin_dow",
        "cos_dow",
        "sin_month",
        "cos_month",
        "is_holiday",
        "promotion",
        "lag_1d",
        "lag_2d",
        "lag_7d",
        "lag_14d",
        "rolling_7d_mean",
        "rolling_7d_std",
        "rolling_14d_mean",
        "rolling_28d_mean",
        "item_historical_mean",
    ]

    def __init__(self):
        self.item_historical_stats: Dict[str, float] = {}
        self.category_list: List[str] = []
        self.feature_names: List[str] = []

    def fit_transform(
        self, df: pd.DataFrame
    ) -> pd.DataFrame:
        """Fit statistical baselines on the dataset and generate the full feature matrix.

        Args:
            df: Clean DataFrame containing required operational columns.

        Returns:
            DataFrame with enriched feature columns and target 'target_qty_sold'.
        """
        # Ensure chronological ordering
        df = df.sort_values(by=["date", "item_name"]).reset_index(drop=True)

        # 1. Financial derived features
        df["margin"] = np.round(df["price"] - df["cost"], 2)
        df["margin_pct"] = np.round((df["margin"] / df["price"]) * 100.0, 2)

        # 2. Calendar and cyclical features
        df["day_of_week"] = df["date"].dt.day_of_week
        df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)
        df["month"] = df["date"].dt.month
        df["day_of_month"] = df["date"].dt.day

        # Cyclical transforms (smooth calendar continuity)
        df["sin_dow"] = np.sin(2 * np.pi * df["day_of_week"] / 7.0)
        df["cos_dow"] = np.cos(2 * np.pi * df["day_of_week"] / 7.0)
        df["sin_month"] = np.sin(2 * np.pi * df["month"] / 12.0)
        df["cos_month"] = np.cos(2 * np.pi * df["month"] / 12.0)

        # Holiday & Promotion flags (if present, else defaults)
        if "is_holiday" not in df.columns:
            df["is_holiday"] = 0
        if "promotion" not in df.columns:
            df["promotion"] = 0

        # 3. Lags & Rolling features grouped strictly by item
        # Notice: shift(1) guarantees that yesterday's sales are the latest known!
        grouped = df.groupby("item_name")["qty_sold"]

        df["lag_1d"] = grouped.shift(1)
        df["lag_2d"] = grouped.shift(2)
        df["lag_7d"] = grouped.shift(7)
        df["lag_14d"] = grouped.shift(14)

        # Rolling statistics (using shift(1) to avoid including same-day sales)
        shifted_sales = grouped.shift(1)
        df["rolling_7d_mean"] = shifted_sales.groupby(df["item_name"]).transform(
            lambda s: s.rolling(window=7, min_periods=1).mean()
        )
        df["rolling_7d_std"] = shifted_sales.groupby(df["item_name"]).transform(
            lambda s: s.rolling(window=7, min_periods=1).std()
        ).fillna(0.0)
        df["rolling_14d_mean"] = shifted_sales.groupby(df["item_name"]).transform(
            lambda s: s.rolling(window=14, min_periods=1).mean()
        )
        df["rolling_28d_mean"] = shifted_sales.groupby(df["item_name"]).transform(
            lambda s: s.rolling(window=28, min_periods=1).mean()
        )

        # 4. Global Item Baseline
        self.item_historical_stats = df.groupby("item_name")["qty_sold"].mean().to_dict()
        df["item_historical_mean"] = df["item_name"].map(self.item_historical_stats)

        # Impute missing lag values for earliest dates using item historical mean
        for col in ["lag_1d", "lag_2d", "lag_7d", "lag_14d", "rolling_7d_mean", "rolling_14d_mean", "rolling_28d_mean"]:
            df[col] = df[col].fillna(df["item_historical_mean"])

        df["rolling_7d_std"] = df["rolling_7d_std"].fillna(0.0)

        # 5. One-hot encode category
        self.category_list = sorted(df["category"].unique().tolist())
        cat_dummies = pd.get_dummies(df["category"], prefix="cat", drop_first=False, dtype=int)
        df = pd.concat([df, cat_dummies], axis=1)

        # Register complete feature list
        self.feature_names = self.NUMERICAL_COLS + list(cat_dummies.columns)

        # Set target column
        df["target_qty_sold"] = df["qty_sold"]

        return df

    def split_chronological(
        self,
        df: pd.DataFrame,
        train_ratio: float = 0.70,
        val_ratio: float = 0.15,
    ) -> Tuple[pd.DataFrame, pd.Series, pd.DataFrame, pd.Series, pd.DataFrame, pd.Series, Dict[str, Any]]:
        """Split dataset into chronological Train, Validation, and Test sets.

        Args:
            df: Feature-engineered dataframe.
            train_ratio: Proportion of dates for training (default 0.70).
            val_ratio: Proportion of dates for validation (default 0.15).

        Returns:
            (X_train, y_train, X_val, y_val, X_test, y_test, split_metadata)
        """
        unique_dates = np.sort(df["date"].unique())
        n_dates = len(unique_dates)

        train_cutoff_idx = int(n_dates * train_ratio)
        val_cutoff_idx = int(n_dates * (train_ratio + val_ratio))

        train_cutoff_date = unique_dates[train_cutoff_idx]
        val_cutoff_date = unique_dates[val_cutoff_idx]

        train_mask = df["date"] < train_cutoff_date
        val_mask = (df["date"] >= train_cutoff_date) & (df["date"] < val_cutoff_date)
        test_mask = df["date"] >= val_cutoff_date

        train_df = df[train_mask].copy()
        val_df = df[val_mask].copy()
        test_df = df[test_mask].copy()

        X_train = train_df[self.feature_names]
        y_train = train_df["target_qty_sold"]

        X_val = val_df[self.feature_names]
        y_val = val_df["target_qty_sold"]

        X_test = test_df[self.feature_names]
        y_test = test_df["target_qty_sold"]

        split_meta = {
            "train_date_range": (train_df["date"].min().strftime("%Y-%m-%d"), train_df["date"].max().strftime("%Y-%m-%d")),
            "val_date_range": (val_df["date"].min().strftime("%Y-%m-%d"), val_df["date"].max().strftime("%Y-%m-%d")),
            "test_date_range": (test_df["date"].min().strftime("%Y-%m-%d"), test_df["date"].max().strftime("%Y-%m-%d")),
            "train_rows": len(train_df),
            "val_rows": len(val_df),
            "test_rows": len(test_df),
            "feature_count": len(self.feature_names),
        }

        return X_train, y_train, X_val, y_val, X_test, y_test, split_meta
