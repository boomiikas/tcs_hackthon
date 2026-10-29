import os
import pandas as pd

raw_dir = "data/raw"
files = ["meal_info.csv", "fulfilment_center_info.csv", "train.csv", "test.csv"]

print("=== RAW DATA INSPECTION ===")
for fname in files:
    fpath = os.path.join(raw_dir, fname)
    if not os.path.exists(fpath):
        print(f"File missing: {fname}")
        continue
    df = pd.read_csv(fpath, nrows=5)
    print(f"\n--- {fname} ---")
    print(f"Columns: {list(df.columns)}")
    print(f"Sample row:\n{df.head(1).to_dict(orient='records')}")

# Full counts and summary for meal_info and fulfilment_center
if os.path.exists(os.path.join(raw_dir, "meal_info.csv")):
    meals = pd.read_csv(os.path.join(raw_dir, "meal_info.csv"))
    print(f"\nTotal meals: {len(meals)}")
    print("Meal categories:", meals["category"].unique())
    print("Meal cuisines:", meals["cuisine"].unique())
    print(meals.head(10))

if os.path.exists(os.path.join(raw_dir, "fulfilment_center_info.csv")):
    centers = pd.read_csv(os.path.join(raw_dir, "fulfilment_center_info.csv"))
    print(f"\nTotal centers: {len(centers)}")
    print("Center types:", centers["center_type"].unique())
    print(centers.head(5))

if os.path.exists(os.path.join(raw_dir, "train.csv")):
    train_head = pd.read_csv(os.path.join(raw_dir, "train.csv"), nrows=1000)
    print("\nTrain sample info:")
    print(train_head.info())
    print("Weeks range (sample):", train_head["week"].min(), "to", train_head["week"].max())
    print("num_orders describe (sample):")
    print(train_head["num_orders"].describe())
