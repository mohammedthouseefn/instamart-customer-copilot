from pathlib import Path
import pandas as pd

# Location of raw CSV files
DATA_DIR = Path("data/raw")

# Load the three raw tables
customers = pd.read_csv(DATA_DIR / "customers.csv")
products = pd.read_csv(DATA_DIR / "products.csv")
orders = pd.read_csv(DATA_DIR / "orders.csv")

tables = {
    "CUSTOMERS": customers,
    "PRODUCTS": products,
    "ORDERS": orders
}

# 1. Report shape, data types and missing values
for table_name, df in tables.items():
    print(f"\n{'=' * 60}")
    print(f"{table_name} DATA AUDIT")
    print(f"{'=' * 60}")

    print("\nShape (rows, columns):")
    print(df.shape)

    print("\nData types:")
    print(df.dtypes)

    print("\nMissing values:")
    missing = pd.DataFrame({
        "missing_count": df.isnull().sum(),
        "missing_percentage": (
            df.isnull().sum() / len(df) * 100
        ).round(2)
    })

    print(missing)


# 2. Specific audit figures for orders
numeric_amount = pd.to_numeric(
    orders["order_amount"], errors="coerce"
)

numeric_delivery = pd.to_numeric(
    orders["delivery_minutes"], errors="coerce"
)

order_audit = {
    "Raw order rows": len(orders),
    "Exact duplicate rows": orders.duplicated().sum(),
    "Pending orders": (
        orders["status"].astype(str).str.strip().str.lower()
        .eq("pending").sum()
    ),
    "Distinct order IDs": orders["order_id"].nunique(),
    "Non-numeric order amounts": numeric_amount.isna().sum(),
    "Negative delivery minutes": numeric_delivery.lt(0).sum(),
    "Blank delivery minutes": (
        orders["delivery_minutes"].isna()
        | orders["delivery_minutes"].astype(str).str.strip().eq("")
    ).sum()
}


# 3. Specific audit figures for customers
numeric_age = pd.to_numeric(customers["age"], errors="coerce")

customer_audit = {
    "Blank ages": (
        customers["age"].isna()
        | customers["age"].astype(str).str.strip().eq("")
    ).sum(),
    "Ages outside 10-100": (
        numeric_age.notna()
        & ((numeric_age < 10) | (numeric_age > 100))
    ).sum(),
    "Distinct raw city spellings": (
        customers.loc[
            customers["city"].notna()
            & customers["city"].astype(str).str.strip().ne(""),
            "city"
        ].nunique()
    ),
    "Distinct non-blank raw gender spellings": (
        customers.loc[
            customers["gender"].notna()
            & customers["gender"].astype(str).str.strip().ne(""),
            "gender"
        ].nunique()
    ),
    "Blank genders": (
        customers["gender"].isna()
        | customers["gender"].astype(str).str.strip().eq("")
    ).sum()
}


# 4. Display audit summary
print("\n" + "=" * 60)
print("ORDERS AUDIT SUMMARY")
print("=" * 60)

for key, value in order_audit.items():
    print(f"{key}: {value}")

print("\n" + "=" * 60)
print("CUSTOMERS AUDIT SUMMARY")
print("=" * 60)

for key, value in customer_audit.items():
    print(f"{key}: {value}")