from pathlib import Path
import sqlite3
import pandas as pd

# Define paths
CLEAN_DIR = Path("data/clean")
DB_PATH = Path("data/instamart.db")

# Read cleaned CSV files
customers = pd.read_csv(CLEAN_DIR / "customers.csv")
products = pd.read_csv(CLEAN_DIR / "products.csv")
orders = pd.read_csv(CLEAN_DIR / "orders.csv")

# Store order timestamp in the required format
orders["order_ts"] = (
    pd.to_datetime(orders["order_ts"])
    .dt.strftime("%Y-%m-%d %H:%M:%S")
)

# Create database directory if needed
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# Connect to SQLite database
with sqlite3.connect(DB_PATH) as connection:

    # Save DataFrames as SQLite tables
    customers.to_sql(
        "customers", connection,
        if_exists="replace", index=False
    )

    products.to_sql(
        "products", connection,
        if_exists="replace", index=False
    )

    orders.to_sql(
        "orders", connection,
        if_exists="replace", index=False
    )

    # Verify table names and row counts
    print("Database created successfully!")

    tables = ["customers", "products", "orders"]

    for table in tables:
        count = pd.read_sql_query(
            f"SELECT COUNT(*) AS total FROM {table}",
            connection
        ).iloc[0]["total"]

        print(f"{table}: {count} rows")

print(f"\nDatabase location: {DB_PATH}")