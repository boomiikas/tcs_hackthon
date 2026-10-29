"""Item-level demand prediction models, training, evaluation, and inference for CanteenIQ."""

import os
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, root_mean_squared_error, r2_score
from sklearn.inspection import permutation_importance
import joblib


def calculate_wape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Calculate Weighted Absolute Percentage Error (WAPE).

    WAPE = sum(|y - y_hat|) / sum(y)
    Safely handles division by zero when actual total demand is zero.
    """
    total_actual = float(np.sum(y_true))
    total_error = float(np.sum(np.abs(y_true - y_pred)))
    if total_actual <= 1e-6:
        return 0.0 if total_error <= 1e-6 else 1.0
    return round(total_error / total_actual, 4)


class BaselineRegressor:
    """Simple temporal baseline: uses lag-7 (same day last week) with fallback to 7-day rolling mean."""

    def __init__(self):
        self.is_fitted = False

    def fit(self, X: pd.DataFrame, y: pd.Series):
        self.is_fitted = True
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        # Use lag_7d if present, else fallback to rolling_7d_mean or item_historical_mean
        preds = []
        for _, row in X.iterrows():
            val = row.get("lag_7d", np.nan)
            if pd.isna(val) or val < 0:
                val = row.get("rolling_7d_mean", np.nan)
            if pd.isna(val) or val < 0:
                val = row.get("item_historical_mean", 10.0)
            preds.append(max(0.0, float(val)))
        return np.array(preds)


class DemandModelSuite:
    """Trains, compares, and packages baseline, Random Forest, and Gradient Boosting models."""

    def __init__(self, random_state: int = 42):
        self.random_state = random_state
        self.models: Dict[str, Any] = {}
        self.model_metrics: Dict[str, Dict[str, float]] = {}
        self.best_model_name: Optional[str] = None
        self.best_model: Optional[Any] = None
        self.lower_quantile_model: Optional[HistGradientBoostingRegressor] = None
        self.upper_quantile_model: Optional[HistGradientBoostingRegressor] = None
        self.feature_names: List[str] = []
        self.feature_importance: Dict[str, float] = {}
        self.per_item_test_metrics: Dict[str, Dict[str, float]] = {}

    def train_and_evaluate_all(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_val: pd.DataFrame,
        y_val: pd.Series,
        X_test: pd.DataFrame,
        y_test: pd.Series,
        test_df_context: Optional[pd.DataFrame] = None,
    ) -> Dict[str, Any]:
        """Train Candidate Models, validate, select best, and evaluate on unseen Test set."""
        self.feature_names = list(X_train.columns)

        # 1. Define Candidate Models
        candidates = {
            "Seasonal Naive Baseline (Lag-7)": BaselineRegressor(),
            "Random Forest Regressor": RandomForestRegressor(
                n_estimators=100,
                max_depth=12,
                min_samples_leaf=4,
                n_jobs=-1,
                random_state=self.random_state,
            ),
            "HistGradientBoosting Regressor": HistGradientBoostingRegressor(
                max_iter=150,
                max_depth=8,
                min_samples_leaf=10,
                l2_regularization=1.0,
                random_state=self.random_state,
            ),
        }

        # 2. Fit and Evaluate on Validation Set
        val_results = {}
        for name, model in candidates.items():
            model.fit(X_train, y_train)
            self.models[name] = model

            val_preds = np.maximum(0.0, model.predict(X_val))
            metrics = {
                "MAE": round(float(mean_absolute_error(y_val, val_preds)), 2),
                "RMSE": round(float(root_mean_squared_error(y_val, val_preds)), 2),
                "WAPE": calculate_wape(y_val.values, val_preds),
                "R2": round(float(r2_score(y_val, val_preds)), 3),
            }
            val_results[name] = metrics

        # Select Best Model based on lowest Validation WAPE
        self.best_model_name = min(val_results, key=lambda k: val_results[k]["WAPE"])
        self.best_model = self.models[self.best_model_name]

        # 3. Fit Prediction Intervals (Quantile Regression for Uncertainty)
        # 10th percentile (p10) and 90th percentile (p90)
        self.lower_quantile_model = HistGradientBoostingRegressor(
            loss="quantile", quantile=0.10, max_iter=100, random_state=self.random_state
        ).fit(X_train, y_train)

        self.upper_quantile_model = HistGradientBoostingRegressor(
            loss="quantile", quantile=0.90, max_iter=100, random_state=self.random_state
        ).fit(X_train, y_train)

        # 4. Evaluate Selected Model on Unseen Test Set
        test_preds = np.maximum(0.0, self.best_model.predict(X_test))
        test_metrics = {
            "MAE": round(float(mean_absolute_error(y_test, test_preds)), 2),
            "RMSE": round(float(root_mean_squared_error(y_test, test_preds)), 2),
            "WAPE": calculate_wape(y_test.values, test_preds),
            "R2": round(float(r2_score(y_test, test_preds)), 3),
        }

        # 5. Compute Feature Importance (Tree or Permutation)
        if hasattr(self.best_model, "feature_importances_"):
            importances = self.best_model.feature_importances_
            self.feature_importance = dict(
                sorted(zip(self.feature_names, map(lambda v: round(float(v), 4), importances)), key=lambda x: -x[1])
            )
        else:
            # Fallback to permutation importance
            perm = permutation_importance(self.best_model, X_val, y_val, n_repeats=5, random_state=self.random_state)
            self.feature_importance = dict(
                sorted(zip(self.feature_names, map(lambda v: round(float(max(0, v)), 4), perm.importances_mean)), key=lambda x: -x[1])
            )

        # 6. Per-Item Test Set Breakdown
        if test_df_context is not None and "item_name" in test_df_context.columns:
            test_df_eval = test_df_context.copy()
            test_df_eval["actual"] = y_test.values
            test_df_eval["predicted"] = np.round(test_preds, 1)

            per_item = {}
            for item, grp in test_df_eval.groupby("item_name"):
                if len(grp) >= 5:
                    item_actual = grp["actual"].values
                    item_pred = grp["predicted"].values
                    per_item[item] = {
                        "count": len(grp),
                        "mean_actual": round(float(grp["actual"].mean()), 1),
                        "mean_predicted": round(float(grp["predicted"].mean()), 1),
                        "MAE": round(float(mean_absolute_error(item_actual, item_pred)), 2),
                        "WAPE": calculate_wape(item_actual, item_pred),
                    }
            self.per_item_test_metrics = per_item

        return {
            "validation_comparison": val_results,
            "selected_best_model": self.best_model_name,
            "test_performance": test_metrics,
            "top_10_features": dict(list(self.feature_importance.items())[:10]),
            "per_item_performance_sample": dict(list(self.per_item_test_metrics.items())[:5]),
        }

    def save_artifacts(self, filepath: str = "ml/artifacts/demand_model.joblib") -> str:
        """Save trained models, preprocessors, and metadata to disk."""
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "best_model_name": self.best_model_name,
            "best_model": self.best_model,
            "lower_quantile_model": self.lower_quantile_model,
            "upper_quantile_model": self.upper_quantile_model,
            "feature_names": self.feature_names,
            "feature_importance": self.feature_importance,
            "per_item_metrics": self.per_item_test_metrics,
        }
        joblib.dump(payload, filepath)
        return str(Path(filepath).resolve())

    @classmethod
    def load_artifacts(cls, filepath: str = "ml/artifacts/demand_model.joblib") -> "DemandModelSuite":
        """Load persisted models and artifacts."""
        payload = joblib.load(filepath)
        suite = cls()
        suite.best_model_name = payload["best_model_name"]
        suite.best_model = payload["best_model"]
        suite.lower_quantile_model = payload.get("lower_quantile_model")
        suite.upper_quantile_model = payload.get("upper_quantile_model")
        suite.feature_names = payload["feature_names"]
        suite.feature_importance = payload.get("feature_importance", {})
        suite.per_item_test_metrics = payload.get("per_item_metrics", {})
        return suite
