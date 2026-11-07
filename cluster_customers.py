
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

# Load RFM data
rfm = pd.read_csv("outputs/rfm.csv")

features = ["recency", "frequency", "monetary"]
X = rfm[features]

# Standardise RFM features
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Evaluate K from 2 to 8
results = []

for k in range(2, 9):
    model = KMeans(
        n_clusters=k,
        n_init=10,
        random_state=42
    )

    labels = model.fit_predict(X_scaled)

    inertia = model.inertia_
    silhouette = silhouette_score(X_scaled, labels)

    results.append({
        "K": k,
        "Inertia": round(inertia, 2),
        "Silhouette": round(silhouette, 3)
    })

# Display results
results_df = pd.DataFrame(results)

print("\n=== K-Means Evaluation ===")
print(results_df.to_string(index=False))
