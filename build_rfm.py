
import pandas as pd
from pathlib import Path

# Snapshot date specified in the assignment
SNAPSHOT_DATE = pd.Timestamp("2025-10-01 00:00:00")

# Load cleaned data
orders = pd.read_csv("data/clean/orders.csv")

# Use completed orders only
completed = orders[orders["status"] == "completed"].copy()

# Convert order timestamp to datetime
completed["order_ts"] = pd.to_datetime(completed["order_ts"])

# Calculate RFM metrics for each customer
rfm = (
    completed
    .groupby("customer_id")
    .agg(
        last_order_ts=("order_ts", "max"),
        frequency=("order_id", "nunique"),
        monetary=("order_amount", "sum")
    )
    .reset_index()
)

# Recency = whole days since the last completed order
rfm["recency"] = (
    SNAPSHOT_DATE - rfm["last_order_ts"]
).dt.days

# Remove the intermediate timestamp column
rfm = rfm[
    ["customer_id", "recency", "frequency", "monetary"]
]

# Create output folder and save RFM table
Path("outputs").mkdir(exist_ok=True)

rfm.to_csv("outputs/rfm.csv", index=False)

# Display summary statistics
print("RFM table created successfully!")
print(f"Total customers: {len(rfm)}")

print("\n=== RFM Summary ===")
print(rfm[["recency", "frequency", "monetary"]].agg(
    ["median", "min", "max", "mean"]
).round(2))

print("\nSaved to: outputs/rfm.csv")
