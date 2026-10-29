# MenuMind — AI-Powered Canteen Menu Mix Optimization
## Realistic Synthetic College-Canteen Dataset & MenuMind Rewind Simulator

---

### Executive Overview

**MenuMind** is an AI-powered canteen menu mix optimization platform designed to eliminate food waste while maximizing student satisfaction and cafeteria profitability. Its signature capability, **MenuMind Rewind: The Counterfactual Food Waste Simulator**, enables cafeteria operators, food service managers, and academic administrators to retrospectively test alternative menu preparation policies against real-world customer demand.

This pipeline grounds synthetic data generation directly upon real-world consumer demand patterns from the **Kaggle Food Demand Forecasting dataset**, transforming macro-level warehouse order histories into a high-fidelity, item-level daily college-canteen operational dataset.

---

## 1. Source Dataset & Data Lineage

- **Source Reference**: [Kaggle Food Demand Forecasting Challenge](https://www.kaggle.com/datasets/kannanaikkal/food-demand-forecasting)
- **Source Directory**: `data/raw/`
- **Data Integrity Guarantee**: Source CSV files are treated as strictly immutable and are never overwritten or fabricated.

| Source File | Raw Rows | Key Columns | Purpose |
| :--- | :--- | :--- | :--- |
| `train.csv` | 456,548 | `id`, `week`, `center_id`, `meal_id`, `checkout_price`, `base_price`, `emailer_for_promotion`, `homepage_featured`, `num_orders` | Historical weekly demand signal, pricing variations, and promotions |
| `meal_info.csv` | 51 | `meal_id`, `category`, `cuisine` | Grounding for dish categories (14) and cuisines (4) |
| `fulfilment_center_info.csv` | 77 | `center_id`, `city_code`, `region_code`, `center_type`, `op_area` | Fulfillment center physical footprint metadata |
| `test.csv` | 32,573 | `id`, `week`, `center_id`, `meal_id`, `checkout_price`, `base_price`, etc. | Unused in generation; preserved for forecasting benchmarks |

*If the source dataset has not been downloaded, obtain `archive.zip` from Kaggle and place `meal_info.csv`, `fulfilment_center_info.csv`, and `train.csv` directly into `data/raw/`.*

---

## 2. Realistic Disaggregation & Generation Methodology

The Kaggle dataset captures weekly orders at regional fulfillment centers. A direct naive assignment would be unrepresentative of a physical campus cafeteria. MenuMind implements a 5-stage transformation pipeline:

```
[Kaggle Weekly Center Orders]
             │
             ▼ (Demand Scaling: 0.15x to college canteen level)
[Weekly Canteen Baseline]
             │
             ▼ (Hare-Niemeyer Integer Disaggregation across 7 Days)
[Base Daily Demand Shares (Weekly Total Preserved 100%)]
             │
             ▼ (Dynamic Multipliers: Calendar Events, Holidays, Promo Uplift, Price Elasticity, Ratings)
[Simulated Ground-Truth Daily Demand Estimate (D_t)]
             │
             ▼ (Kitchen Policy: Buffered Moving Average + Chef Estimation Error + Batch Cooking)
[Simulated Chef Preparation Decision (Q_t)]
             │
             ▼ (Operational Accounting Identities)
[Realized Sales, Leftover Waste, Stockouts, Revenue, Profit & Regret]
```

### Key Realism Mechanics:

1. **Integer Preservation Disaggregation (Hare-Niemeyer Method)**:
   Base weekly orders $W_{i, w}$ are scaled to canteen levels ($W \times 0.15$). Then, using category-specific day-of-week probability distributions perturbed via a Dirichlet distribution ($\kappa = 80$), daily integer portions are apportioned using the **Largest Remainder Method**. This guarantees:
   $$\sum_{d=0}^{6} \text{daily\_demand}_d = W_{i, w} \quad \text{exactly}$$

2. **College Academic Calendar & Campus Dynamics**:
   A 52-week calendar models campus reality:
   - **Regular Term**: Weekday lunch peaks (Mon-Thu), Friday cafe/social surge (+20% snacks, beverages, pizza).
   - **Midterms & End-Semester Exams**: Beverage demand surges (+35-40%), heavy meals drop (-15%).
   - **Campus Cultural Fest & Tech Hackathons**: Campus footfall surges (+45-65% for pizzas, quick bites, cold brew).
   - **Summer/Winter Vacations & National Holidays**: Operational footprint drops by 70-80%.

3. **Promotions & Category Price Elasticity**:
   Promotions introduce a configurable demand uplift (default $+25\%$). Price sensitivity is modeled per category ($\epsilon_{\text{beverage}} = -1.2$, $\epsilon_{\text{pizza}} = -1.1$, $\epsilon_{\text{rice\_bowl}} = -0.7$). Discounts increase demand:
   $$\text{Demand} \propto 1 + |\epsilon| \times \frac{P_{\text{base}} - P_{\text{checkout}}}{P_{\text{base}}}$$

4. **Human Kitchen Preparation Heuristics**:
   Unlike synthetic datasets that generate waste randomly, waste in MenuMind arises naturally from the mismatch between chef prep decisions and realized demand. In `buffered_forecast` mode:
   - The chef plans based on recent rolling demand.
   - Applies a $+10\%$ safety buffer to protect against stockouts.
   - Suffers human estimation bias ($\pm 8\%$ Gaussian error).
   - Produces in kitchen cooking batches (e.g. increments of 5 portions).

---

## 3. Strict Operational Accounting Identities

On every simulated day $t$ and item $i$, the following identities hold without exception:

$$\begin{aligned}
\text{qty\_sold} &= \min(\text{demand\_estimate}, \text{qty\_prepared}) \\
\text{qty\_wasted} &= \max(0, \text{qty\_prepared} - \text{qty\_sold}) \\
\text{stockout\_flag} &= \mathbf{1}_{(\text{demand\_estimate} > \text{qty\_prepared})} \\
\text{missed\_demand} &= \max(0, \text{demand\_estimate} - \text{qty\_prepared}) \\
\text{qty\_sold} + \text{qty\_wasted} &= \text{qty\_prepared} \quad (\text{Conservation of Mass}) \\
\text{revenue} &= \text{qty\_sold} \times \text{selling\_price} \\
\text{preparation\_cost} &= \text{qty\_prepared} \times \text{unit\_cost} \\
\text{waste\_cost} &= \text{qty\_wasted} \times (\text{unit\_cost} + \text{waste\_disposal\_cost}) \\
\text{profit} &= \text{revenue} - \text{preparation\_cost} - (\text{qty\_wasted} \times \text{waste\_disposal\_cost})
\end{aligned}$$

*Note: Unit cost is accounted for when items are prepared; wasted food incurs an additional disposal fee ($\text{INR } 2.00/\text{portion}$), eliminating double-counting.*

---

## 4. MenuMind Rewind: Retrospective Counterfactual Simulator

MenuMind Rewind allows canteen managers to answer: **"What if we had prepared a different quantity or used an AI recommendation engine?"**

For any candidate preparation quantity $Q$:
- $\text{Sales}(Q) = \min(D, Q)$
- $\text{Waste}(Q) = \max(0, Q - D)$
- $\text{Missed Demand}(Q) = \max(0, D - Q)$
- $\text{Profit}(Q) = \text{Sales}(Q) \cdot P - Q \cdot C - \text{Waste}(Q) \cdot C_{\text{disp}}$

### Regret Quantification:
The ex-post optimal hindsight decision is $Q^* = D$, achieving maximum profit $\text{Profit}^* = D \cdot (P - C)$. Regret metrics measure deviation from optimal:
- **Profit Regret**: $\text{Profit}^* - \text{Profit}(Q)$ (always $\ge 0$).
- **Waste Regret**: $\text{Waste}(Q) \cdot (C + C_{\text{disp}})$ (wasted funds due to over-preparation).
- **Missed Demand Regret**: $\text{Missed Demand}(Q) \cdot (P - C)$ (unrealized gross margin due to under-preparation).

---

## 5. Output File Schema Reference

All processed files are generated in `data/processed/`:

### 1. `synthetic_canteen_daily.csv` (16,814 rows)
Primary item-level daily transactional dataset.

| Column | Type | Description |
| :--- | :--- | :--- |
| `date` | String | Operating service date (`YYYY-MM-DD`) |
| `week_number` | Integer | Operating week number (1 to 52) |
| `day_of_week` | String | Day of week (`Monday` to `Sunday`) |
| `is_holiday` | Integer | Holiday indicator (1 = holiday/break, 0 = academic day) |
| `campus_event` | String | Campus event (`Cultural Fest`, `Exams`, `Normal`, etc.) |
| `item_id` | String | Synthetic unique item ID (`MM-1062`, `MM-1109`, etc.) |
| `item_name` | String | Plausible synthetic dish name matching category/cuisine |
| `original_meal_id` | Integer | Traceable Kaggle source meal ID |
| `category` | String | Food category (`Beverages`, `Rice Bowl`, `Pizza`, etc.) |
| `cuisine` | String | Cuisine type (`Indian`, `Italian`, `Thai`, `Continental`) |
| `selling_price` | Float | Price per portion charged to students (INR) |
| `cost` | Float | Preparation/ingredient unit cost per portion (INR) |
| `calories` | Integer | Estimated nutritional calories per portion (kcal) |
| `rating` | Float | Simulated student satisfaction rating (1.0 to 5.0) |
| `promotion` | Integer | Promotion active on this item/day (1 or 0) |
| `demand_estimate` | Integer | Underlying customer demand before preparation limits |
| `qty_prepared` | Integer | Portions prepared by the canteen kitchen |
| `qty_sold` | Integer | Portions sold to students |
| `qty_wasted` | Integer | Portions left over and wasted |
| `stockout_flag` | Integer | Whether demand exceeded prepared quantity (1 or 0) |
| `missed_demand` | Integer | Unserved student demand |
| `revenue` | Float | Gross revenue earned (`qty_sold * selling_price`) |
| `preparation_cost`| Float | Total cost of food prepared (`qty_prepared * cost`) |
| `waste_cost` | Float | Financial waste cost including disposal fees |
| `profit` | Float | Net operating profit from this item-day |

### 2. `synthetic_canteen_weekly.csv` (2,402 rows)
Aggregated weekly dataset for higher-level menu mix optimization.

- Aggregated by `(week_number, item_id, item_name, category, cuisine, original_meal_id)`
- Provides weekly sums for demand, prepared, sold, wasted, missed demand, revenue, profit, and stockout days.

### 3. `synthetic_menu_catalog.csv` (51 items)
Master menu catalog for FastAPI endpoints and Streamlit UI.

- Includes `item_id`, `item_name`, `original_meal_id`, `category`, `cuisine`, `selling_price`, `cost`, `margin`, `margin_pct`, `calories`, `base_rating`, `popularity_tier`, `price_elasticity`.

### 4. `source_mapping.csv` (51 items)
Traceability matrix connecting Kaggle source meals with synthetic items.

- Includes historical mean orders, historical price benchmarks, and transformation audit notes.

### 5. `generation_summary.json`
Complete reproducibility metadata, source row counts, seed, date range, validation test logs, and summary KPIs.

---

## 6. How to Run the Pipeline

### Prerequisites
Activate the project's Python virtual environment:
```powershell
.\.venv\Scripts\Activate.ps1
```

### 1. Generate the Synthetic Dataset
```powershell
python scripts/generate_synthetic_data.py --random-seed 42 --num-weeks 52 --demand-scale 0.15
```

Optional CLI Flags:
- `--prep-policy`: `buffered_forecast` (default), `naive_last_week`, `oracle`, `static_capacity`
- `--buffer-pct`: Safety buffer percentage (e.g. `0.10` for +10%)
- `--waste-disposal-cost`: Disposal fee (e.g. `2.0`)
- `--promo-uplift`: Promotional lift fraction (e.g. `0.25`)
- `--start-date`: Starting Monday (default: `2025-01-06`)
- `--output-dir`: Target folder (default: `data/processed`)

### 2. Run Data Validation
```powershell
python scripts/validate_synthetic_data.py
```

### 3. Run the MenuMind Rewind Simulation Demo
```powershell
python scripts/demo_rewind_simulator.py
```

### 4. Run Automated Unit Tests
```powershell
python -m pytest tests/
```

---

## 7. Current Dataset Summary Statistics (Seed 42)

- **Daily Records**: 16,814
- **Weekly Records**: 2,402
- **Unique Menu Items**: 48 active across 52 weeks (out of 51 catalog items)
- **Simulated Date Range**: `2025-01-06` to `2026-01-04` (364 operating days)
- **Total Portions Prepared**: 289,825
- **Total Portions Sold**: 182,242
- **Total Portions Wasted**: 107,583
- **Simulated Chef Waste Rate**: 37.12%
- **Stockout Rate**: 18.54% of service days
- **Total Net Operating Profit**: INR 12,305,557.69
- **MenuMind Rewind Potential**:
  - Waste reduced from **107,583** to **54,163** portions (**-49.7% reduction!**)
  - Additional Net Profit Unlocked: **+INR 12,118,265.24**

---

## 8. Assumptions and Limitations

1. **Synthetic Nature**: While demand shapes and relative dish popularities are grounded in real Kaggle food ordering patterns, day-of-week disaggregations and event calendar spikes are synthetic simulations.
2. **Shelf Life**: The baseline simulation assumes freshly prepared hot items must be served on the day of cooking (1-day shelf life). Packaged beverages and ambient snacks could realistically carry inventory over to subsequent days.
3. **Capacity Constraints**: The kitchen preparation simulator currently assumes flexible kitchen equipment capacity. Upper batch bounds can be integrated into future constrained linear programming solvers in MenuMind.
