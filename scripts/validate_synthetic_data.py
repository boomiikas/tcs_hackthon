"""Standalone validation script for MenuMind processed synthetic canteen data."""

import sys
import argparse
from pathlib import Path
import pandas as pd
import json

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Ensure robust unicode output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from src.validator import SyntheticDataValidator


def main():
    parser = argparse.ArgumentParser(
        description="MenuMind Synthetic Data Automated Validation Suite"
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default="data/processed",
        help="Directory containing the generated processed CSV files (default: data/processed)",
    )
    parser.add_argument(
        "--waste-disposal-cost",
        type=float,
        default=2.0,
        help="Waste disposal unit cost used during generation (default: 2.0)",
    )
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    print("=" * 70)
    print("   MENUMIND: SYNTHETIC CANTEEN DATASET VALIDATION SUITE")
    print("=" * 70)
    print(f"Target Directory: {data_dir.resolve()}\n")

    daily_path = data_dir / "synthetic_canteen_daily.csv"
    weekly_path = data_dir / "synthetic_canteen_weekly.csv"
    catalog_path = data_dir / "synthetic_menu_catalog.csv"
    mapping_path = data_dir / "source_mapping.csv"
    summary_path = data_dir / "generation_summary.json"

    # Check existence
    expected_files = [daily_path, weekly_path, catalog_path, mapping_path]
    missing = [str(f.name) for f in expected_files if not f.exists()]
    if missing:
        print(f"[ERROR] Required processed dataset files missing in '{data_dir}': {missing}")
        print("Please run 'python scripts/generate_synthetic_data.py' first.")
        sys.exit(1)

    print("[1/4] Loading generated datasets...")
    daily_df = pd.read_csv(daily_path)
    weekly_df = pd.read_csv(weekly_path)
    catalog_df = pd.read_csv(catalog_path)
    mapping_df = pd.read_csv(mapping_path)

    print(f"  Loaded daily:   {len(daily_df):,} rows")
    print(f"  Loaded weekly:  {len(weekly_df):,} rows")
    print(f"  Loaded catalog: {len(catalog_df):,} items")
    print(f"  Loaded mapping: {len(mapping_df):,} items")

    print("\n[2/4] Executing validation rules...")
    validator = SyntheticDataValidator(waste_disposal_cost=args.waste_disposal_cost)
    passed, report = validator.run_all_checks(
        daily_df=daily_df,
        weekly_df=weekly_df,
        catalog_df=catalog_df,
        mapping_df=mapping_df,
    )

    print("\n[3/4] Validation Results:")
    for section, outcome in report.items():
        if section == "summary":
            continue
        status_str = "[PASS]" if outcome["passed"] else "[FAIL]"
        print(f"\n  {status_str} Section: {section.upper()}")
        for msg in outcome.get("details", []):
            print(f"    - {msg}")

    print("\n[4/4] Descriptive Summary Statistics:")
    print("-" * 50)
    summary = report["summary"]
    for k, v in summary.items():
        print(f"  {k:30s}: {v}")

    print("\n" + "=" * 70)
    if passed:
        print("   ALL TESTS PASSED! Dataset is certified ready for MenuMind.")
        print("=" * 70)
        sys.exit(0)
    else:
        print("   VALIDATION FAILED! Please inspect errors above.")
        print("=" * 70)
        sys.exit(1)


if __name__ == "__main__":
    main()
