"""Converts weekly demand signals into synthetic daily demand using documented apportionment."""

from typing import Dict, Any, List, Tuple
import numpy as np
import pandas as pd


# Default Day of Week Profile for College Canteen (Monday=0 to Sunday=6)
# Weekdays have full campus footfall; Saturday has partial (labs/hostels); Sunday has resident hostellers.
BASE_DAY_WEIGHTS = {
    0: 0.17,  # Monday
    1: 0.16,  # Tuesday
    2: 0.16,  # Wednesday
    3: 0.15,  # Thursday
    4: 0.19,  # Friday (surge in cafe / social eating)
    5: 0.11,  # Saturday (reduced commuter traffic)
    6: 0.06,  # Sunday (hostel resident traffic)
}

# Category-specific Day-of-Week Multipliers
CATEGORY_DAY_SKEW = {
    "Pizza":        {0: 0.85, 1: 0.90, 2: 0.95, 3: 1.05, 4: 1.35, 5: 1.30, 6: 0.90},
    "Beverages":    {0: 1.10, 1: 1.05, 2: 1.05, 3: 1.00, 4: 1.15, 5: 0.85, 6: 0.70},
    "Rice Bowl":    {0: 1.15, 1: 1.10, 2: 1.10, 3: 1.05, 4: 0.90, 5: 0.85, 6: 0.75},
    "Sandwich":     {0: 1.05, 1: 1.05, 2: 1.00, 3: 1.00, 4: 1.10, 5: 0.95, 6: 0.80},
    "Salad":        {0: 1.25, 1: 1.20, 2: 1.15, 3: 1.05, 4: 0.80, 5: 0.70, 6: 0.60},
    "Biryani":      {0: 0.90, 1: 0.90, 2: 1.00, 3: 1.05, 4: 1.25, 5: 1.20, 6: 1.10},
    "Pasta":        {0: 0.95, 1: 0.95, 2: 1.00, 3: 1.05, 4: 1.20, 5: 1.15, 6: 0.90},
    "Starters":     {0: 0.90, 1: 0.95, 2: 1.00, 3: 1.05, 4: 1.25, 5: 1.20, 6: 0.90},
    "Other Snacks": {0: 0.95, 1: 1.00, 2: 1.00, 3: 1.05, 4: 1.25, 5: 1.10, 6: 0.85},
    "Desert":       {0: 0.90, 1: 0.90, 2: 0.95, 3: 1.00, 4: 1.30, 5: 1.30, 6: 1.00},
    "Soup":         {0: 1.20, 1: 1.15, 2: 1.10, 3: 1.05, 4: 0.85, 5: 0.75, 6: 0.65},
    "Extras":       {0: 1.00, 1: 1.00, 2: 1.00, 3: 1.00, 4: 1.10, 5: 1.05, 6: 0.85},
    "Fish":         {0: 0.90, 1: 0.95, 2: 1.00, 3: 1.05, 4: 1.20, 5: 1.15, 6: 0.95},
    "Seafood":      {0: 0.90, 1: 0.90, 2: 0.95, 3: 1.05, 4: 1.25, 5: 1.20, 6: 0.95},
}


class DemandDisaggregator:
    """Disaggregates weekly Kaggle demand into realistic synthetic daily demand.

    Preserves exact weekly totals during initial apportionment using the Hare-Niemeyer
    (Largest Remainder) integer rounding method.
    """

    def __init__(
        self,
        demand_scale: float = 0.15,
        promo_uplift: float = 0.25,
        random_seed: int = 42,
    ):
        self.demand_scale = demand_scale
        self.promo_uplift = promo_uplift
        self.rng = np.random.RandomState(random_seed)

    def get_normalized_day_weights(self, category: str) -> np.ndarray:
        """Compute normalized 7-day probability weights for a food category."""
        base_w = np.array([BASE_DAY_WEIGHTS[d] for d in range(7)])
        skews = CATEGORY_DAY_SKEW.get(category, {})
        skew_w = np.array([skews.get(d, 1.0) for d in range(7)])
        combined = base_w * skew_w
        return combined / np.sum(combined)

    def disaggregate_weekly_total(
        self,
        weekly_total: int,
        category: str,
        dirichlet_concentration: float = 80.0,
    ) -> np.ndarray:
        """Apportion an integer weekly total into 7 daily non-negative integers.

        Guarantees that sum(daily_shares) == weekly_total exactly, using the
        Largest Remainder (Hare-Niemeyer) method.

        Args:
            weekly_total: Total integer portions for the week.
            category: Food category for day-of-week profile.
            dirichlet_concentration: Controls stochastic week-to-week daily variance.

        Returns:
            np.ndarray of length 7 with integer daily demand portions.
        """
        if weekly_total <= 0:
            return np.zeros(7, dtype=int)

        weights = self.get_normalized_day_weights(category)
        # Stochastic perturbation around the expected profile
        alpha = weights * dirichlet_concentration
        p_shares = self.rng.dirichlet(alpha)

        # Largest Remainder Method (Hare-Niemeyer)
        exact_shares = weekly_total * p_shares
        integer_shares = np.floor(exact_shares).astype(int)
        remainders = exact_shares - integer_shares
        shortfall = weekly_total - int(np.sum(integer_shares))

        if shortfall > 0:
            # Distribute the remaining units to the days with largest remainders
            top_indices = np.argsort(-remainders)[:shortfall]
            integer_shares[top_indices] += 1

        return integer_shares

    def compute_daily_demand_estimate(
        self,
        base_daily_demand: int,
        category: str,
        is_promo: bool,
        event_multiplier: float,
        price_elasticity: float,
        price_discount_ratio: float,
        student_rating: float,
    ) -> int:
        """Compute realized underlying daily demand estimate incorporating all behavioral drivers.

        Args:
            base_daily_demand: Integer portion from weekly disaggregation.
            category: Food category.
            is_promo: Whether promotional boost applies.
            event_multiplier: Academic calendar / event multiplier.
            price_elasticity: Item price elasticity coefficient (e.g. -1.1).
            price_discount_ratio: (base_price - checkout_price) / base_price (>= 0).
            student_rating: Item student rating (1-5 scale).

        Returns:
            Simulated daily demand estimate (integer >= 0).
        """
        if base_daily_demand <= 0:
            return 0

        # 1. Academic Event effect
        d_sim = float(base_daily_demand) * event_multiplier

        # 2. Promotional Uplift
        if is_promo:
            d_sim *= (1.0 + self.promo_uplift)

        # 3. Price Elasticity Uplift (if price is discounted below base)
        if price_discount_ratio > 0.001:
            # elasticity is negative, discount is positive -> demand increases
            elasticity_factor = 1.0 + abs(price_elasticity) * price_discount_ratio
            d_sim *= min(elasticity_factor, 1.50)  # capped at +50%

        # 4. Student Rating Appeal: +/- 5% per 0.5 star deviation from 4.0
        rating_factor = 1.0 + 0.05 * (student_rating - 4.0)
        d_sim *= max(0.80, min(rating_factor, 1.20))

        # 5. Stochastic daily unobserved variance (Normal noise, std=0.06)
        noise = self.rng.normal(0.0, 0.06)
        d_sim *= max(0.5, (1.0 + noise))

        return max(0, int(round(d_sim)))
