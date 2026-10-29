"""Configuration management for MenuMind Synthetic Data Generation Pipeline."""

from dataclasses import dataclass, field, asdict
import argparse
import json
from pathlib import Path
from typing import Optional, Dict, Any


@dataclass
class MenuMindConfig:
    """Configuration parameters for synthetic canteen data generation and simulation."""

    # Reproducibility
    random_seed: int = 42

    # Calendar & Scope
    start_date: str = "2025-01-06"  # Monday
    num_weeks: int = 52            # 52 weeks = 364 operating days
    center_id: int = 13            # Source center (Center 13 covers all 51 meals)
    num_items: int = 51            # Number of unique menu items (up to 51)

    # Scaling & Realism
    demand_scale: float = 0.15     # Scale warehouse demand down to college canteen volume
    price_scale: float = 1.0       # Price scaling factor (1.0 preserves realistic INR pricing)
    promo_uplift: float = 0.25     # +25% demand boost during active promotions
    waste_disposal_cost: float = 2.0  # Disposal fee per unsold wasted portion (INR)

    # Kitchen Preparation Policy
    prep_policy: str = "buffered_forecast"  # 'buffered_forecast', 'naive_last_week', 'oracle', 'static_capacity'
    buffer_pct: float = 0.10       # Safety buffer over baseline forecast (+10%)
    kitchen_batch_size: int = 5    # Portions cooked in batches of 5

    # File Paths
    raw_dir: str = "data/raw"
    output_dir: str = "data/processed"

    # College context
    canteen_name: str = "Campus Central Cafeteria"
    academic_year: str = "2025-2026"

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to serializable dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MenuMindConfig":
        """Load config from dictionary."""
        valid_keys = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)

    @classmethod
    def from_json(cls, json_path: str) -> "MenuMindConfig":
        """Load config from a JSON file."""
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)

    def save_json(self, json_path: str) -> None:
        """Persist config to a JSON file."""
        Path(json_path).parent.mkdir(parents=True, exist_ok=True)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)


def parse_cli_args() -> MenuMindConfig:
    """Parse command line arguments and return a MenuMindConfig instance."""
    parser = argparse.ArgumentParser(
        description="MenuMind — Realistic Synthetic Canteen Dataset Generator & Simulator"
    )
    parser.add_argument(
        "--random-seed",
        type=int,
        default=42,
        help="Random seed for deterministic generation (default: 42)",
    )
    parser.add_argument(
        "--start-date",
        type=str,
        default="2025-01-06",
        help="Synthetic start date YYYY-MM-DD (default: 2025-01-06, a Monday)",
    )
    parser.add_argument(
        "--num-weeks",
        type=int,
        default=52,
        help="Number of operating weeks to generate (default: 52)",
    )
    parser.add_argument(
        "--center-id",
        type=int,
        default=13,
        help="Source fulfilment center ID to base demand upon (default: 13)",
    )
    parser.add_argument(
        "--num-items",
        type=int,
        default=51,
        help="Number of synthetic items to include (default: 51)",
    )
    parser.add_argument(
        "--demand-scale",
        type=float,
        default=0.15,
        help="Demand scaling factor to convert warehouse demand to canteen level (default: 0.15)",
    )
    parser.add_argument(
        "--price-scale",
        type=float,
        default=1.0,
        help="Scaling factor for selling prices (default: 1.0)",
    )
    parser.add_argument(
        "--promo-uplift",
        type=float,
        default=0.25,
        help="Proportional demand increase during promotions (default: 0.25)",
    )
    parser.add_argument(
        "--waste-disposal-cost",
        type=float,
        default=2.0,
        help="Unit cost of disposing wasted food (default: 2.0)",
    )
    parser.add_argument(
        "--prep-policy",
        type=str,
        default="buffered_forecast",
        choices=["buffered_forecast", "naive_last_week", "oracle", "static_capacity"],
        help="Kitchen preparation policy (default: buffered_forecast)",
    )
    parser.add_argument(
        "--buffer-pct",
        type=float,
        default=0.10,
        help="Safety buffer fraction above forecast (default: 0.10)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=5,
        dest="kitchen_batch_size",
        help="Batch cooking portion increment (default: 5)",
    )
    parser.add_argument(
        "--raw-dir",
        type=str,
        default="data/raw",
        help="Directory containing source CSV files (default: data/raw)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/processed",
        help="Directory to save generated CSV and JSON files (default: data/processed)",
    )
    parser.add_argument(
        "--config-file",
        type=str,
        default=None,
        help="Path to optional JSON configuration file overriding defaults",
    )

    args = parser.parse_args()

    # Load from config file first if provided
    if args.config_file and Path(args.config_file).exists():
        cfg = MenuMindConfig.from_json(args.config_file)
        # Apply any explicitly passed CLI flags
        for k, v in vars(args).items():
            if k not in ("config_file",) and v is not None:
                # check if k was explicitly passed on sys.argv
                import sys
                arg_flag = f"--{k.replace('_', '-')}"
                if any(a.startswith(arg_flag) for a in sys.argv):
                    setattr(cfg, k, v)
        return cfg

    # Otherwise construct from parsed arguments
    return MenuMindConfig(
        random_seed=args.random_seed,
        start_date=args.start_date,
        num_weeks=args.num_weeks,
        center_id=args.center_id,
        num_items=args.num_items,
        demand_scale=args.demand_scale,
        price_scale=args.price_scale,
        promo_uplift=args.promo_uplift,
        waste_disposal_cost=args.waste_disposal_cost,
        prep_policy=args.prep_policy,
        buffer_pct=args.buffer_pct,
        kitchen_batch_size=args.kitchen_batch_size,
        raw_dir=args.raw_dir,
        output_dir=args.output_dir,
    )
