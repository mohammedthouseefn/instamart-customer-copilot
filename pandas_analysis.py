import pandas as pd

customers = pd.read_csv("data/clean/customers.csv")
products = pd.read_csv("data/clean/products.csv")
orders = pd.read_csv("data/clean/orders.csv")

# Keep only completed orders
completed = orders[orders["status"] == "completed"]

# Join all three datasets
merged = (
    completed
    .merge(customers[["customer_id", "city"]], on="customer_id")
    .merge(products[["product_id", "category"]], on="product_id")
)

# Rebuild SQL Q2 using Pandas pivot_table
pivot = pd.pivot_table(
    merged,
    values="order_amount",
    index="city",
    columns="category",
    aggfunc="sum",
    fill_value=0,
    margins=True,
    margins_name="Total"
)

print("\n=== Revenue by City and Category ===")
print(pivot.round(2).to_string())

print("\nSQL Q2 Expected Total: ₹2,998,668.80")
print(f"Pandas Total: ₹{pivot.loc['Total', 'Total']:,.2f}")

# City-level aggregation
city_summary = (
    completed
    .merge(customers[["customer_id", "city"]], on="customer_id")
    .groupby("city")
    .agg(
        total_revenue=("order_amount", "sum"),
        average_order_value=("order_amount", "mean"),
        order_count=("order_id", "count")
    )
    .reset_index()
)

print("\n=== City-level Order Analysis ===")
print(city_summary.round(2).to_string(index=False))

# Order amount distribution
amount = completed["order_amount"]

print("\n=== Order Amount Statistics ===")
print(f"Mean: {amount.mean():.2f}")
print(f"Median: {amount.median():.2f}")
print(f"Skewness: {amount.skew():.2f}")

# IQR outlier detection
q1 = amount.quantile(0.25)
q3 = amount.quantile(0.75)
iqr = q3 - q1

lower_bound = q1 - 1.5 * iqr
upper_bound = q3 + 1.5 * iqr

outliers = amount[
    (amount < lower_bound) | (amount > upper_bound)
]

print(f"Q1: {q1:.2f}")
print(f"Q3: {q3:.2f}")
print(f"IQR: {iqr:.2f}")
print(f"Lower bound: {lower_bound:.2f}")
print(f"Upper bound: {upper_bound:.2f}")
print(f"Outlier count: {len(outliers)}")

# Correlation analysis
correlation_columns = [
    "order_amount",
    "discount_pct",
    "quantity",
    "delivery_minutes"
]

correlation = completed[correlation_columns].corr()

print("\n=== Correlation Matrix ===")
print(correlation.round(3).to_string())

# Find strongest correlation (excluding diagonal)
correlation_pairs = correlation.abs().where(
    ~pd.DataFrame(
        [[i == j for j in range(len(correlation_columns))]
         for i in range(len(correlation_columns))],
        index=correlation_columns,
        columns=correlation_columns
    )
)

strongest_pair = correlation_pairs.stack().idxmax()

print("\nStrongest absolute correlation:")
print(f"{strongest_pair[0]} vs {strongest_pair[1]}: "
      f"{correlation.loc[strongest_pair[0], strongest_pair[1]]:.3f}")