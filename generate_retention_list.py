import pandas as pd
import joblib

from sklearn.model_selection import train_test_split

# Load datasets and selected model
df = pd.read_csv("outputs/lapse_dataset.csv")
segments = pd.read_csv("outputs/customer_segments.csv")
model = joblib.load("outputs/lapse_model.joblib")

# Recreate the original test split
_, test_df = train_test_split(
    df,
    test_size=0.2,
    stratify=df["lapsed"],
    random_state=42
)

# Identify premium customers in the test set
premium_test = test_df.merge(
    segments[["customer_id", "is_premium"]],
    on="customer_id",
    how="inner"
)

premium_test = premium_test[
    premium_test["is_premium"] == True
].copy()

# Prepare model features in the original training order
feature_columns = model.feature_names_in_.tolist()
X_premium = premium_test[feature_columns]

# Calculate lapse probabilities
premium_test["lapse_probability"] = (
    model.predict_proba(X_premium)[:, 1]
)

# Select top 10 customers
retention_list = (
    premium_test[
        ["customer_id", "lapse_probability", "lapsed"]
    ]
    .rename(columns={"lapsed": "actually_lapsed"})
    .sort_values("lapse_probability", ascending=False)
    .head(10)
)

# Save results
retention_list.to_csv(
    "outputs/retention_list.csv",
    index=False
)

print("=== Top 10 Premium Customers for Retention ===")
print(retention_list.to_string(index=False))

print("\nTotal premium customers in test set:", len(premium_test))
print(
    "Actually lapsed among top 10:",
    retention_list["actually_lapsed"].sum()
)

print("\nRetention list saved successfully!")