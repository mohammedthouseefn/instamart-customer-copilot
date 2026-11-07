from pathlib import Path
import pandas as pd

# Define file paths
RAW_DIR = Path("data/raw")
CLEAN_DIR = Path("data/clean")

# Create clean directory
CLEAN_DIR.mkdir(parents=True, exist_ok=True)

# Load customers data
customers = pd.read_csv(RAW_DIR / "customers.csv")

print("Before cleaning:", customers.shape)

# 1. Standardise city names
customers["city"] = customers["city"].str.strip().str.title()

# 2. Standardise gender values
gender_mapping = {
    "m": "male",
    "male": "male",
    "man": "male",
    "f": "female",
    "female": "female",
    "woman": "female"
}

customers["gender"] = (
    customers["gender"]
    .fillna("")
    .str.strip()
    .str.lower()
    .map(gender_mapping)
    .fillna("unknown")
)

# 3. Convert age to numeric
customers["age"] = pd.to_numeric(
    customers["age"], errors="coerce"
)

# Treat ages outside 10-100 as missing
customers.loc[
    ~customers["age"].between(10, 100),
    "age"
] = float("nan")

# Fill missing ages using city median
customers["age"] = customers["age"].fillna(
    customers.groupby("city")["age"].transform("median")
)

# 4. Convert signup_date to datetime
customers["signup_date"] = pd.to_datetime(
    customers["signup_date"]
)

# Save cleaned customers
customers.to_csv(
    CLEAN_DIR / "customers.csv",
    index=False
)

# Display results
print("\nAfter cleaning:", customers.shape)

print("\nCity counts:")
print(customers["city"].value_counts())

print("\nGender counts:")
print(customers["gender"].value_counts())

print("\nMissing ages:", customers["age"].isna().sum())

print(
    "\nAge range:",
    customers["age"].min(),
    "-",
    customers["age"].max()
)

print("\nCleaned customers saved successfully!")

# ==========================================
# ORDERS DATA CLEANING
# ==========================================

# Load raw products and orders
products = pd.read_csv(RAW_DIR / "products.csv")
orders = pd.read_csv(RAW_DIR / "orders.csv")

print("\nBefore orders cleaning:", orders.shape)

# 1. Convert order_ts to datetime
orders["order_ts"] = pd.to_datetime(orders["order_ts"])

# 2. Remove exact duplicate rows
orders = orders.drop_duplicates()

print("After removing exact duplicates:", orders.shape)

# 3. Keep the latest record for each order_id
orders = orders.sort_values(
    "order_ts", kind="mergesort"
)

orders = orders.drop_duplicates(
    subset=["order_id"], keep="last"
).reset_index(drop=True)

# Add product category and price temporarily
product_lookup = products[
    ["product_id", "category", "price_inr"]
]

orders = orders.merge(
    product_lookup,
    on="product_id",
    how="left"
)

print("After removing duplicate order IDs:", orders.shape)

# 4. Convert order_amount to numeric
orders["order_amount"] = pd.to_numeric(
    orders["order_amount"], errors="coerce"
)

# Calculate missing amounts using product price
calculated_amount = (
    orders["price_inr"]
    * orders["quantity"]
    * (1 - orders["discount_pct"] / 100)
).round(2)

orders["order_amount"] = (
    orders["order_amount"].fillna(calculated_amount)
)

# 5. Convert delivery_minutes to numeric
orders["delivery_minutes"] = pd.to_numeric(
    orders["delivery_minutes"], errors="coerce"
)

# Replace negative delivery times with missing values
orders.loc[
    orders["delivery_minutes"] < 0,
    "delivery_minutes"
] = float("nan")

# 6. Fill missing delivery times for completed orders
# using the median of the same product category

completed = orders["status"].eq("completed")

category_medians = (
    orders["delivery_minutes"]
    .where(completed)
    .groupby(orders["category"])
    .transform("median")
)

missing_completed = (
    completed & orders["delivery_minutes"].isna()
)

orders.loc[
    missing_completed, "delivery_minutes"
] = category_medians[missing_completed]

# 7. Keep cancelled order delivery times missing
cancelled = orders["status"].eq("cancelled")

orders.loc[
    cancelled, "delivery_minutes"
] = float("nan")

# Remove temporary product columns
orders = orders.drop(columns=["category", "price_inr"])

# Save cleaned products and orders
products.to_csv(
    CLEAN_DIR / "products.csv",
    index=False
)

orders.to_csv(
    CLEAN_DIR / "orders.csv",
    index=False
)

# Display final results
print("\n========== ORDERS CLEANING RESULTS ==========")

print("Final order shape:", orders.shape)

print("\nOrder status counts:")
print(orders["status"].value_counts())

print(
    "\nMissing order amounts:",
    orders["order_amount"].isna().sum()
)

print(
    "Missing delivery times in completed orders:",
    orders.loc[completed, "delivery_minutes"].isna().sum()
)

print(
    "Missing delivery times in cancelled orders:",
    orders.loc[cancelled, "delivery_minutes"].isna().sum()
)

print(
    "\nCompleted order revenue: INR",
    round(orders.loc[completed, "order_amount"].sum(), 2)
)

print("\nCleaned orders and products saved successfully!")