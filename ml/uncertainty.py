"""Demand uncertainty, calibrated prediction intervals, and forecast risk scoring for CanteenIQ."""

from typing import Dict, Any, List, Tuple, Optional
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor


class DemandUncertaintyEstimator:
    """Estimates demand prediction intervals (P10, P50, P90) with empirical conformal calibration

    and provides forecast risk assessments for kitchen preparation.
    """

    def __init__(self, random_state: int = 42):
        self.random_state = random_state
        self.p10_model: Optional[HistGradientBoostingRegressor] = None
        self.p50_model: Optional[HistGradientBoostingRegressor] = None
        self.p90_model: Optional[HistGradientBoostingRegressor] = None
        self.conformal_margin: float = 0.0
        self.validation_coverage: float = 0.0
        self.validation_mean_width: float = 0.0

    def fit(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_val: Optional[pd.DataFrame] = None,
        y_val: Optional[pd.Series] = None,
        target_nominal_coverage: float = 0.80,
    ) -> "DemandUncertaintyEstimator":
        """Train quantile regressors and optionally calibrate intervals on validation data."""
        # 1. Train Quantile Regressors
        self.p10_model = HistGradientBoostingRegressor(
            loss="quantile", quantile=0.10, max_iter=120, min_samples_leaf=10, random_state=self.random_state
        ).fit(X_train, y_train)

        self.p50_model = HistGradientBoostingRegressor(
            loss="quantile", quantile=0.50, max_iter=120, min_samples_leaf=10, random_state=self.random_state
        ).fit(X_train, y_train)

        self.p90_model = HistGradientBoostingRegressor(
            loss="quantile", quantile=0.90, max_iter=120, min_samples_leaf=10, random_state=self.random_state
        ).fit(X_train, y_train)

        # 2. Conformal Calibration on Validation Data
        if X_val is not None and y_val is not None and len(y_val) > 0:
            raw_p10 = np.maximum(0.0, self.p10_model.predict(X_val))
            raw_p90 = np.maximum(raw_p10, self.p90_model.predict(X_val))

            # Conformity scores: distance outside the raw interval
            scores = np.maximum(y_val.values - raw_p90, raw_p10 - y_val.values)
            # Find the quantile of errors matching target nominal coverage (80%)
            self.conformal_margin = float(np.quantile(scores, target_nominal_coverage))

            calib_p10 = np.maximum(0.0, raw_p10 - max(0.0, self.conformal_margin))
            calib_p90 = raw_p90 + max(0.0, self.conformal_margin)

            inside = (y_val.values >= calib_p10) & (y_val.values <= calib_p90)
            self.validation_coverage = float(np.mean(inside) * 100.0)
            self.validation_mean_width = float(np.mean(calib_p90 - calib_p10))

        return self

    def predict_intervals(
        self,
        X: pd.DataFrame,
        point_predictions: Optional[np.ndarray] = None,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Predict calibrated lower (P10), median (P50), and upper (P90) demand bounds.

        Returns:
            Tuple of (p10_bounds, p50_medians, p90_bounds)
        """
        raw_p10 = np.maximum(0.0, self.p10_model.predict(X))
        raw_p50 = np.maximum(0.0, self.p50_model.predict(X))
        raw_p90 = np.maximum(raw_p10, self.p90_model.predict(X))

        # Apply conformal margin for calibrated coverage
        p10 = np.maximum(0.0, raw_p10 - max(0.0, self.conformal_margin))
        p90 = np.maximum(p10, raw_p90 + max(0.0, self.conformal_margin))

        # Enforce consistency: p10 <= p50 <= p90
        p50 = np.clip(raw_p50, p10, p90)

        # If external point predictions provided (e.g. from mean regressor), align bounds around it
        if point_predictions is not None:
            p10 = np.minimum(p10, point_predictions)
            p90 = np.maximum(p90, point_predictions)

        return np.round(p10, 1), np.round(p50, 1), np.round(p90, 1)

    def evaluate_test_coverage(
        self,
        X_test: pd.DataFrame,
        y_test: pd.Series,
    ) -> Dict[str, Any]:
        """Evaluate empirical interval coverage and metrics on held-out test data."""
        p10, p50, p90 = self.predict_intervals(X_test)
        y = y_test.values

        # Empirical coverage
        inside = (y >= p10) & (y <= p90)
        coverage_pct = round(float(np.mean(inside) * 100.0), 2)

        # Interval width
        widths = p90 - p10
        mean_width = round(float(np.mean(widths)), 2)
        median_width = round(float(np.median(widths)), 2)

        # Winkler Score (Interval Score) for 80% intervals (alpha = 0.20)
        alpha = 0.20
        under_penalty = (2.0 / alpha) * np.maximum(0.0, p10 - y)
        over_penalty = (2.0 / alpha) * np.maximum(0.0, y - p90)
        winkler_scores = widths + under_penalty + over_penalty
        mean_winkler = round(float(np.mean(winkler_scores)), 2)

        # Identify risky items
        relative_widths = widths / np.maximum(1.0, p50)
        high_risk_count = int(np.sum(relative_widths > 1.5))

        return {
            "target_nominal_coverage_pct": 80.0,
            "empirical_test_coverage_pct": coverage_pct,
            "mean_interval_width_portions": mean_width,
            "median_interval_width_portions": median_width,
            "mean_winkler_score": mean_winkler,
            "conformal_calibration_margin": round(self.conformal_margin, 2),
            "high_uncertainty_forecast_count": high_risk_count,
            "risk_guidance": (
                "Notice: A prediction interval [P10, P90] represents statistical bounds capturing expected "
                "daily fluctuations under normal operating conditions. It is not an absolute physical guarantee "
                "against sudden exogenous campus disruptions (e.g. unscheduled closures, severe weather)."
            ),
        }

    def assess_forecast_risk(
        self,
        predicted_demand: float,
        p10: float,
        p90: float,
        shelf_life_days: int = 1,
    ) -> Dict[str, Any]:
        """Classify operational forecast risk for a single dish preparation decision."""
        spread = p90 - p10
        rel_spread = spread / max(1.0, predicted_demand)

        if rel_spread > 1.5 or spread >= 18:
            risk_level = "HIGH_UNCERTAINTY"
            recommendation = (
                f"High volatility detected (P10={p10}, P90={p90}). Recommend lean initial batch "
                "with midday preparation review to protect against surplus waste."
            )
        elif rel_spread > 0.8 or spread >= 8:
            risk_level = "MODERATE_UNCERTAINTY"
            recommendation = "Moderate variance. Apply standard +10% buffer with batch cooking."
        else:
            risk_level = "LOW_UNCERTAINTY"
            recommendation = "Stable demand pattern. High confidence in predicted portion requirement."

        return {
            "risk_level": risk_level,
            "p10_pessimistic": p10,
            "p90_surge": p90,
            "interval_spread_portions": round(spread, 1),
            "relative_spread_ratio": round(rel_spread, 2),
            "operational_recommendation": recommendation,
        }
