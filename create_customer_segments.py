import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA

# Load RFM data
rfm = pd.read_csv("outputs/rfm.csv")

# Select features
features = ["recency", "frequency", "monetary"]
X = rfm[features]

# Scale features
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Train final K-Means model
kmeans = KMeans(
    n_clusters=4,
    n_init=10,
    random_state=42
)

rfm["segment_id"] = kmeans.fit_predict(X_scaled)

# Generate segment profiles
profile = rfm.groupby("segment_id").agg(
    customer_count=("customer_id", "count"),
    avg_recency=("recency", "mean"),
    avg_frequency=("frequency", "mean"),
    avg_monetary=("monetary", "mean")
).round(2)

print("=== Customer Segment Profiles ===")
print(profile)

print("\n=== Segment Sizes ===")
print(rfm["segment_id"].value_counts().sort_index())

# Assign business-friendly segment names
segment_names = {
    0: "Occasional Customers",
    1: "Premium Customers",
    2: "Loyal Customers",
    3: "At-Risk Customers"
}

rfm["segment_name"] = rfm["segment_id"].map(segment_names)

# Identify premium customers
rfm["is_premium"] = rfm["segment_id"] == 1

# Save customer segments
rfm.to_csv("outputs/customer_segments.csv", index=False)

print("\nCustomer segments saved successfully!")
print("Premium customers:", rfm["is_premium"].sum())

# PCA: Reduce RFM features to 2 dimensions
pca = PCA(n_components=2)
X_pca = pca.fit_transform(X_scaled)

explained_variance = pca.explained_variance_ratio_

print("\n=== PCA Analysis ===")
print(f"Principal Component 1: {explained_variance[0]:.3f}")
print(f"Principal Component 2: {explained_variance[1]:.3f}")
print(f"Total Explained Variance: {explained_variance.sum():.3f}")