import pandas as pd
from pathlib import Path

# Date boundaries
CUTOFF_DATE = pd.Timestamp("2025-09-01")
OUTCOME_END_DATE = pd.Timestamp("2025-10-01")

# Load cleaned data
orders = pd.read_csv("data/clean/orders.csv", parse_dates=["order_ts"])
customers = pd.read_csv("data/clean/customers.csv", parse_dates=["signup_date"])
products = pd.read_csv("data/clean/products.csv")

# Add product category to orders
orders = orders.merge(
    products[["product_id", "category"]],
    on="product_id",
    how="left"
)

# Separate historical orders and outcome-period orders
historical = orders[orders["order_ts"] < CUTOFF_DATE].copy()

completed_history = historical[
    historical["status"] == "completed"
].copy()

outcome_orders = orders[
    (orders["order_ts"] >= CUTOFF_DATE)
    & (orders["order_ts"] < OUTCOME_END_DATE)
    & (orders["status"] == "completed")
]

# Cohort: customers with at least one completed historical order
cohort_ids = completed_history["customer_id"].unique()

# Historical completed-order features
features = completed_history.groupby("customer_id").agg(
    last_order_ts=("order_ts", "max"),
    frequency=("order_id", "nunique"),
    monetary=("order_amount", "sum"),
    avg_discount_pct=("discount_pct", "mean"),
    avg_delivery_minutes=("delivery_minutes", "mean")
)

# Recency as of cutoff date
features["recency"] = (
    CUTOFF_DATE - features["last_order_ts"]
).dt.days

# Cancellation rate from all historical orders
total_orders = historical.groupby("customer_id").size()
cancelled_orders = historical[
    historical["status"] == "cancelled"
].groupby("customer_id").size()

features["cancellation_rate"] = (
    cancelled_orders.reindex(cohort_ids, fill_value=0)
    / total_orders.reindex(cohort_ids)
)

# Most frequently purchased product category
favourite_category = (
    completed_history.groupby("customer_id")["category"]
    .agg(lambda values: values.mode().iloc[0])
)

features["favourite_category"] = favourite_category

# Customer demographics
customer_features = customers[
    ["customer_id", "city", "age", "gender", "signup_date"]
].set_index("customer_id")

features = features.join(customer_features)

# Customer tenure as of cutoff date
features["tenure_days"] = (
    CUTOFF_DATE - features["signup_date"]
).dt.days

# Lapse label: no completed order during September 2025
active_ids = set(outcome_orders["customer_id"].unique())

features["lapsed"] = (
    ~features.index.isin(active_ids)
).astype(int)

# Remove intermediate columns
features = features.drop(columns=["last_order_ts", "signup_date"])

# Save dataset
features = features.reset_index()

Path("outputs").mkdir(exist_ok=True)

features.to_csv("outputs/lapse_dataset.csv", index=False)

# Summary
print("=== Lapse Dataset Summary ===")
print("Total customers:", len(features))
print("Lapsed customers:", features["lapsed"].sum())
print("Not-lapsed customers:", (features["lapsed"] == 0).sum())
print("Lapse percentage:", round(features["lapsed"].mean() * 100, 2), "%")

print("\n=== Feature Columns ===")
print(features.columns.tolist())

print("\n=== Missing Values ===")
print(features.isnull().sum())

print("\nSaved to: outputs/lapse_dataset.csv")