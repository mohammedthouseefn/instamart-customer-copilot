from pathlib import Path
import sqlite3
import pandas as pd

# File paths
CLEAN_DIR = Path("data/clean")
DB_PATH = Path("data/instamart.db")

# Load cleaned CSV files
customers = pd.read_csv(CLEAN_DIR / "customers.csv")
products = pd.read_csv(CLEAN_DIR / "products.csv")
orders = pd.read_csv(CLEAN_DIR / "orders.csv")

# Load SQLite database tables
with sqlite3.connect(DB_PATH) as connection:
    db_customers = pd.read_sql_query(
        "SELECT * FROM customers", connection
    )
    db_products = pd.read_sql_query(
        "SELECT * FROM products", connection
    )
    db_orders = pd.read_sql_query(
        "SELECT * FROM orders", connection
    )

# Define validation checkpoints
checks = {
    "Customer count": len(customers) == 1200,

    "Product count": len(products) == 40,

    "Order count": len(orders) == 12309,

    "Customer city counts": customers["city"].value_counts().to_dict() == {
        "Pune": 227,
        "Delhi": 210,
        "Bengaluru": 197,
        "Chennai": 191,
        "Hyderabad": 191,
        "Mumbai": 184
    },

    "Customer gender counts": customers["gender"].value_counts().to_dict() == {
        "female": 610,
        "male": 560,
        "unknown": 30
    },

    "No missing customer ages": customers["age"].isna().sum() == 0,

    "Customer age range": (
        customers["age"].min() == 18
        and customers["age"].max() == 60
    ),

    "Completed order count": (
        orders["status"].eq("completed").sum() == 11110
    ),

    "Cancelled order count": (
        orders["status"].eq("cancelled").sum() == 1199
    ),

    "No pending orders": (
        orders["status"].eq("pending").sum() == 0
    ),

    "No missing order amounts": (
        orders["order_amount"].isna().sum() == 0
    ),

    "No missing completed delivery times": (
        orders.loc[
            orders["status"].eq("completed"),
            "delivery_minutes"
        ].isna().sum() == 0
    ),

    "Cancelled delivery times remain missing": (
        orders.loc[
            orders["status"].eq("cancelled"),
            "delivery_minutes"
        ].isna().sum() == 1199
    ),

    "Completed revenue": abs(
        orders.loc[
            orders["status"].eq("completed"),
            "order_amount"
        ].sum() - 2998668.80
    ) < 0.01,

    "SQLite customer count": len(db_customers) == 1200,

    "SQLite product count": len(db_products) == 40,

    "SQLite order count": len(db_orders) == 12309
}

# Display validation results
failed_checks = []

for name, passed in checks.items():
    if passed:
        print(f"PASS: {name}")
    else:
        print(f"FAIL: {name}")
        failed_checks.append(name)

# Final result
if failed_checks:
    print("\nFailed checkpoints:", failed_checks)
    raise SystemExit(1)

print("ALL CHECKPOINTS PASSED")