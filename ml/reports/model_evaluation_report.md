# CanteenIQ — Demand Prediction Model Evaluation Report

## 1. Chronological Split Setup (Leakage Prevention)

- **Train Period**: 2025-01-06 to 2025-09-16 (11,607 rows)
- **Validation Period**: 2025-09-17 to 2025-11-10 (2,581 rows)
- **Unseen Test Period**: 2025-11-11 to 2026-01-04 (2,626 rows)
- **Features Used**: 38 features (Lags shifted >= 1 day, no same-day sales/waste leakage)

## 2. Validation Set Model Comparison

| Model Candidate | MAE (portions) | RMSE | WAPE (%) | R² Score |
| :--- | :--- | :--- | :--- | :--- |
| **Seasonal Naive Baseline (Lag-7)** | 7.39 | 15.99 | 65.0% | 0.161 |
| **Random Forest Regressor** | 3.41 | 7.38 | 30.0% | 0.821 |
| **HistGradientBoosting Regressor** | 3.31 | 7.99 | 29.1% | 0.791 |

### Selected Best Model: **HistGradientBoosting Regressor**

## 3. Test Set Performance on Unseen Future Service Dates

- **Mean Absolute Error (MAE)**: 3.17 portions
- **Root Mean Squared Error (RMSE)**: 7.08 portions
- **Weighted Absolute Percentage Error (WAPE)**: **30.7%**
- **R² Coefficient of Determination**: 0.800

## 4. Top 10 Influential Demand Drivers

| Feature | Relative Importance |
| :--- | :--- |
| `lag_1d` | 0.5512 |
| `day_of_week` | 0.0815 |
| `is_holiday` | 0.0587 |
| `item_historical_mean` | 0.0373 |
| `rolling_7d_mean` | 0.0360 |
| `sin_dow` | 0.0208 |
| `lag_2d` | 0.0132 |
| `promotion` | 0.0088 |
| `rolling_28d_mean` | 0.0042 |
| `lag_7d` | 0.0031 |

## 5. Sample Per-Item Forecast Accuracy

| Item Name | Observations | Mean Actual | Mean Predicted | MAE | WAPE (%) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Baked Spinach & Ricotta Lasagna | 48 | 2.0 | 2.5 | 1.09 | 54.6% |
| Balsamic Caprese Pasta Salad | 55 | 4.6 | 4.2 | 1.45 | 31.2% |
| Belgian Chocolate Frappe | 55 | 7.5 | 6.3 | 2.54 | 34.1% |
| Cheesy Alfredo Fusilli Pasta | 55 | 1.9 | 1.9 | 0.93 | 47.7% |
| Classic Cold Hazelnut Mocha | 55 | 28.7 | 27.0 | 7.25 | 25.2% |

## 6. Demand Uncertainty & Empirical Prediction Interval Coverage [P10, P90]

- **Target Nominal Coverage**: 80.0%
- **Empirical Test Set Coverage**: **81.84%**
- **Mean Interval Width**: 8.73 portions
- **Median Interval Width**: 5.50 portions
- **Mean Winkler Interval Score**: 14.14
- **High Uncertainty Forecasts Detected**: 859 dishes

> **Risk Guidance**: Notice: A prediction interval [P10, P90] represents statistical bounds capturing expected daily fluctuations under normal operating conditions. It is not an absolute physical guarantee against sudden exogenous campus disruptions (e.g. unscheduled closures, severe weather).

