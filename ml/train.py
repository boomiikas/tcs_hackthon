"""End-to-end training and evaluation script for CanteenIQ demand forecasting."""

import sys
import argparse
from pathlib import Path
import json
from typing import Dict, Any
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Console encoding guard
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from ml.data_loader import CanteenDataLoader
from ml.preprocessing import CanteenFeatureEngineer
from ml.eda import CanteenEDA
from ml.demand_model import DemandModelSuite
from ml.uncertainty import DemandUncertaintyEstimator
import joblib


def run_training_pipeline(
    data_path: str = "data/processed/synthetic_canteen_daily.csv",
    artifact_dir: str = "ml/artifacts",
    report_dir: str = "ml/reports",
) -> Dict[str, Any]:
    print("=" * 70)
    print("   CANTEENIQ: ML DEMAND FORECASTING TRAINING PIPELINE")
    print("=" * 70)

    # 1. Load and Validate Data
    print("\n[Step 1/5] Loading and validating canteen operational data...")
    loader = CanteenDataLoader(filepath=data_path)
    clean_df, audit = loader.load_and_validate()
    print(f"  Loaded {len(clean_df):,} validated records ({audit['start_date']} to {audit['end_date']})")
    print(f"  Dishes: {audit['unique_items']} | Categories: {audit['unique_categories']} | Days: {audit['total_days']}")

    # 2. Run Exploratory Data Analysis & Waste Audit
    print("\n[Step 2/5] Running Exploratory Data Analysis & Waste Audit...")
    eda = CanteenEDA(clean_df, output_dir=report_dir)
    eda_summary = eda.generate_full_report()
    print(f"  Overall Kitchen Waste Rate: {eda_summary['macro_kpis']['overall_waste_percentage']}%")
    print(f"  Total Food Waste Cost: INR {eda_summary['macro_kpis']['total_waste_cost_inr']:,.2f}")
    print(f"  Reports saved to: {report_dir}/eda_report.md & {report_dir}/eda_summary.json")

    # 3. Feature Engineering & Strict Chronological Split
    print("\n[Step 3/5] Engineering features and preparing chronological train/val/test splits...")
    fe = CanteenFeatureEngineer()
    enriched_df = fe.fit_transform(clean_df)
    X_train, y_train, X_val, y_val, X_test, y_test, split_meta = fe.split_chronological(enriched_df)

    print(f"  Features engineered: {len(fe.feature_names)}")
    print(f"  Train Split: {split_meta['train_rows']:,} rows ({split_meta['train_date_range'][0]} to {split_meta['train_date_range'][1]})")
    print(f"  Val Split:   {split_meta['val_rows']:,} rows ({split_meta['val_date_range'][0]} to {split_meta['val_date_range'][1]})")
    print(f"  Test Split:  {split_meta['test_rows']:,} rows ({split_meta['test_date_range'][0]} to {split_meta['test_date_range'][1]})")

    # 4. Train Models, Validate, and Select Best
    print("\n[Step 4/5] Training candidate models & tuning prediction intervals...")
    suite = DemandModelSuite(random_state=42)
    test_context = clean_df[clean_df["date"] >= split_meta["test_date_range"][0]].copy()

    results = suite.train_and_evaluate_all(
        X_train=X_train,
        y_train=y_train,
        X_val=X_val,
        y_val=y_val,
        X_test=X_test,
        y_test=y_test,
        test_df_context=test_context,
    )

    print("\n  --- Validation Comparison ---")
    val_df = pd.DataFrame(results["validation_comparison"]).T
    print(val_df.to_string())

    print(f"\n  >>> SELECTED BEST MODEL: {results['selected_best_model']}")
    print(f"  --- Test Set Performance on Unseen Future Data ---")
    for k, v in results["test_performance"].items():
        print(f"    {k:8s}: {v}")

    # Train and calibrate prediction intervals
    print("\n  --- Calibrating Demand Uncertainty & Prediction Intervals [P10, P90] ---")
    unc_est = DemandUncertaintyEstimator(random_state=42)
    unc_est.fit(X_train=X_train, y_train=y_train, X_val=X_val, y_val=y_val, target_nominal_coverage=0.80)
    unc_test_eval = unc_est.evaluate_test_coverage(X_test=X_test, y_test=y_test)
    results["uncertainty_evaluation"] = unc_test_eval

    print(f"    Target Nominal Coverage:   {unc_test_eval['target_nominal_coverage_pct']}%")
    print(f"    Empirical Test Coverage:   {unc_test_eval['empirical_test_coverage_pct']}%")
    print(f"    Mean Interval Width:       {unc_test_eval['mean_interval_width_portions']} portions")
    print(f"    Mean Winkler Score:        {unc_test_eval['mean_winkler_score']}")
    print(f"    High Uncertainty Forecasts: {unc_test_eval['high_uncertainty_forecast_count']}")

    # 5. Persist Model Artifacts and Save Reports
    print("\n[Step 5/5] Persisting trained artifacts and generating evaluation reports...")
    art_path = Path(artifact_dir) / "demand_model.joblib"
    suite.save_artifacts(filepath=str(art_path))

    fe_path = Path(artifact_dir) / "feature_engineer.joblib"
    joblib.dump(fe, fe_path)

    unc_path = Path(artifact_dir) / "uncertainty_estimator.joblib"
    joblib.dump(unc_est, unc_path)

    # Save detailed evaluation markdown
    eval_md_path = Path(report_dir) / "model_evaluation_report.md"
    _write_evaluation_markdown(results, split_meta, eval_md_path)

    metrics_json_path = Path(report_dir) / "model_metrics.json"
    with open(metrics_json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"  Artifacts saved:")
    print(f"    - {art_path}")
    print(f"    - {fe_path}")
    print(f"    - {unc_path}")
    print(f"  Evaluation report saved:")
    print(f"    - {eval_md_path}")
    print("\n" + "=" * 70)
    print("   TRAINING & EVALUATION PIPELINE COMPLETED SUCCESSFULLY!")
    print("=" * 70)

    return results


def _write_evaluation_markdown(results: Dict[str, Any], split_meta: Dict[str, Any], filepath: Path) -> None:
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("# CanteenIQ — Demand Prediction Model Evaluation Report\n\n")
        f.write("## 1. Chronological Split Setup (Leakage Prevention)\n\n")
        f.write(f"- **Train Period**: {split_meta['train_date_range'][0]} to {split_meta['train_date_range'][1]} ({split_meta['train_rows']:,} rows)\n")
        f.write(f"- **Validation Period**: {split_meta['val_date_range'][0]} to {split_meta['val_date_range'][1]} ({split_meta['val_rows']:,} rows)\n")
        f.write(f"- **Unseen Test Period**: {split_meta['test_date_range'][0]} to {split_meta['test_date_range'][1]} ({split_meta['test_rows']:,} rows)\n")
        f.write(f"- **Features Used**: {split_meta['feature_count']} features (Lags shifted >= 1 day, no same-day sales/waste leakage)\n\n")

        f.write("## 2. Validation Set Model Comparison\n\n")
        f.write("| Model Candidate | MAE (portions) | RMSE | WAPE (%) | R² Score |\n")
        f.write("| :--- | :--- | :--- | :--- | :--- |\n")
        for m_name, m_metrics in results["validation_comparison"].items():
            f.write(f"| **{m_name}** | {m_metrics['MAE']:.2f} | {m_metrics['RMSE']:.2f} | {m_metrics['WAPE'] * 100:.1f}% | {m_metrics['R2']:.3f} |\n")
        f.write("\n")

        f.write(f"### Selected Best Model: **{results['selected_best_model']}**\n\n")

        f.write("## 3. Test Set Performance on Unseen Future Service Dates\n\n")
        test = results["test_performance"]
        f.write(f"- **Mean Absolute Error (MAE)**: {test['MAE']:.2f} portions\n")
        f.write(f"- **Root Mean Squared Error (RMSE)**: {test['RMSE']:.2f} portions\n")
        f.write(f"- **Weighted Absolute Percentage Error (WAPE)**: **{test['WAPE'] * 100:.1f}%**\n")
        f.write(f"- **R² Coefficient of Determination**: {test['R2']:.3f}\n\n")

        f.write("## 4. Top 10 Influential Demand Drivers\n\n")
        f.write("| Feature | Relative Importance |\n")
        f.write("| :--- | :--- |\n")
        for feat, imp in results["top_10_features"].items():
            f.write(f"| `{feat}` | {imp:.4f} |\n")
        f.write("\n")

        f.write("## 5. Sample Per-Item Forecast Accuracy\n\n")
        f.write("| Item Name | Observations | Mean Actual | Mean Predicted | MAE | WAPE (%) |\n")
        f.write("| :--- | :--- | :--- | :--- | :--- | :--- |\n")
        for it, data in results["per_item_performance_sample"].items():
            f.write(f"| {it} | {data['count']} | {data['mean_actual']:.1f} | {data['mean_predicted']:.1f} | {data['MAE']:.2f} | {data['WAPE'] * 100:.1f}% |\n")
        f.write("\n")

        if "uncertainty_evaluation" in results:
            unc = results["uncertainty_evaluation"]
            f.write("## 6. Demand Uncertainty & Empirical Prediction Interval Coverage [P10, P90]\n\n")
            f.write(f"- **Target Nominal Coverage**: {unc['target_nominal_coverage_pct']}%\n")
            f.write(f"- **Empirical Test Set Coverage**: **{unc['empirical_test_coverage_pct']}%**\n")
            f.write(f"- **Mean Interval Width**: {unc['mean_interval_width_portions']:.2f} portions\n")
            f.write(f"- **Median Interval Width**: {unc['median_interval_width_portions']:.2f} portions\n")
            f.write(f"- **Mean Winkler Interval Score**: {unc['mean_winkler_score']:.2f}\n")
            f.write(f"- **High Uncertainty Forecasts Detected**: {unc['high_uncertainty_forecast_count']} dishes\n")
            f.write(f"\n> **Risk Guidance**: {unc['risk_guidance']}\n\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train CanteenIQ Demand Forecast Models")
    parser.add_argument("--data-path", type=str, default="data/processed/synthetic_canteen_daily.csv")
    parser.add_argument("--artifact-dir", type=str, default="ml/artifacts")
    parser.add_argument("--report-dir", type=str, default="ml/reports")
    args = parser.parse_args()

    run_training_pipeline(
        data_path=args.data_path,
        artifact_dir=args.artifact_dir,
        report_dir=args.report_dir,
    )
