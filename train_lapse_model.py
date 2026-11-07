import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GridSearchCV
from sklearn.ensemble import RandomForestClassifier

df = pd.read_csv("outputs/lapse_dataset.csv")

X = df.drop(columns=["customer_id", "lapsed"])
y = df["lapsed"]

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    stratify=y,
    random_state=42
)

print("=== Train/Test Split ===")
print("Training customers:", len(X_train))
print("Testing customers:", len(X_test))

# Baseline: predict every customer as not lapsed
baseline_predictions = [0] * len(y_test)

print("\n=== Baseline Evaluation ===")
print("Accuracy:", round(accuracy_score(y_test, baseline_predictions), 3))
print("Precision:", round(precision_score(y_test, baseline_predictions, zero_division=0), 3))
print("Recall:", round(recall_score(y_test, baseline_predictions, zero_division=0), 3))
print("F1 Score:", round(f1_score(y_test, baseline_predictions, zero_division=0), 3))
print("Confusion Matrix:")
print(confusion_matrix(y_test, baseline_predictions))

# Separate numerical and categorical features
numeric_features = [
    "frequency",
    "monetary",
    "avg_discount_pct",
    "avg_delivery_minutes",
    "recency",
    "cancellation_rate",
    "age",
    "tenure_days"
]

categorical_features = [
    "favourite_category",
    "city",
    "gender"
]

# Preprocessing pipeline
preprocessor = ColumnTransformer(
    transformers=[
        ("num", StandardScaler(), numeric_features),
        ("cat", OneHotEncoder(handle_unknown="ignore", drop="first"), categorical_features)
    ]
)

# Complete pipeline
pipeline = Pipeline([
    ("preprocessor", preprocessor),
    ("model", LogisticRegression(max_iter=1000))
])

# Hyperparameter tuning
param_grid = {
    "model__C": [0.01, 0.1, 1, 10, 100]
}

grid_search = GridSearchCV(
    pipeline,
    param_grid,
    cv=5,
    scoring="f1",
    n_jobs=-1
)

grid_search.fit(X_train, y_train)

print("\n=== Logistic Regression Results ===")
print("Best C:", grid_search.best_params_["model__C"])
print("Best CV F1:", round(grid_search.best_score_, 3))

# Evaluate on untouched test data
logistic_model = grid_search.best_estimator_
logistic_predictions = logistic_model.predict(X_test)

print("\n=== Logistic Regression Test Evaluation ===")
print("Accuracy:", round(accuracy_score(y_test, logistic_predictions), 3))
print("Precision:", round(precision_score(y_test, logistic_predictions), 3))
print("Recall:", round(recall_score(y_test, logistic_predictions), 3))
print("F1 Score:", round(f1_score(y_test, logistic_predictions), 3))
print("Confusion Matrix:")
print(confusion_matrix(y_test, logistic_predictions))

# Random Forest pipeline
rf_pipeline = Pipeline([
    ("preprocessor", preprocessor),
    ("model", RandomForestClassifier(
        n_estimators=100,
        random_state=42
    ))
])

# Hyperparameter tuning
rf_param_grid = {
    "model__max_depth": [3, 5, 8],
    "model__min_samples_leaf": [5, 10, 20]
}

rf_grid_search = GridSearchCV(
    rf_pipeline,
    rf_param_grid,
    cv=5,
    scoring="f1",
    n_jobs=-1
)

rf_grid_search.fit(X_train, y_train)

print("\n=== Random Forest Results ===")
print("Best parameters:", rf_grid_search.best_params_)
print("Best CV F1:", round(rf_grid_search.best_score_, 3))

# Test evaluation
rf_model = rf_grid_search.best_estimator_
rf_predictions = rf_model.predict(X_test)

print("\n=== Random Forest Test Evaluation ===")
print("Accuracy:", round(accuracy_score(y_test, rf_predictions), 3))
print("Precision:", round(precision_score(y_test, rf_predictions), 3))
print("Recall:", round(recall_score(y_test, rf_predictions), 3))
print("F1 Score:", round(f1_score(y_test, rf_predictions), 3))
print("Confusion Matrix:")
print(confusion_matrix(y_test, rf_predictions))

# Oversample minority class in training data only
train_data = X_train.copy()
train_data["lapsed"] = y_train

majority = train_data[train_data["lapsed"] == 0]
minority = train_data[train_data["lapsed"] == 1]

minority_oversampled = minority.sample(
    n=len(majority),
    replace=True,
    random_state=42
)

balanced_train = pd.concat(
    [majority, minority_oversampled]
).sample(frac=1, random_state=42)

X_train_balanced = balanced_train.drop(columns=["lapsed"])
y_train_balanced = balanced_train["lapsed"]

print("\n=== Oversampling Summary ===")
print(y_train_balanced.value_counts())

# Refit best Logistic Regression using balanced training data
balanced_logistic = grid_search.best_estimator_
balanced_logistic.fit(X_train_balanced, y_train_balanced)

# Evaluate on original untouched test data
balanced_predictions = balanced_logistic.predict(X_test)

print("\n=== Logistic Regression After Oversampling ===")
print("Accuracy:", round(accuracy_score(y_test, balanced_predictions), 3))
print("Precision:", round(precision_score(y_test, balanced_predictions), 3))
print("Recall:", round(recall_score(y_test, balanced_predictions), 3))
print("F1 Score:", round(f1_score(y_test, balanced_predictions), 3))
print("Confusion Matrix:")
print(confusion_matrix(y_test, balanced_predictions))

# Random Forest feature importance
rf_preprocessor = rf_grid_search.best_estimator_.named_steps["preprocessor"]
rf_classifier = rf_grid_search.best_estimator_.named_steps["model"]

feature_names = rf_preprocessor.get_feature_names_out()
importances = rf_classifier.feature_importances_

importance_df = pd.DataFrame({
    "feature": feature_names,
    "importance": importances
}).sort_values("importance", ascending=False)

print("\n=== Top 5 Random Forest Features ===")
print(importance_df.head(5).to_string(index=False))

# Logistic Regression coefficients
logistic_preprocessor = grid_search.best_estimator_.named_steps["preprocessor"]
logistic_classifier = grid_search.best_estimator_.named_steps["model"]

feature_names = logistic_preprocessor.get_feature_names_out()
coefficients = logistic_classifier.coef_[0]

coefficient_df = pd.DataFrame({
    "feature": feature_names,
    "coefficient": coefficients
})

coefficient_df["abs_coefficient"] = (
    coefficient_df["coefficient"].abs()
)

print("\n=== Top 10 Logistic Regression Coefficients ===")
print(
    coefficient_df.sort_values(
        "abs_coefficient", ascending=False
    ).head(10).to_string(index=False)
)

from pathlib import Path

# Save selected Logistic Regression model
Path("outputs").mkdir(exist_ok=True)

joblib.dump(
    grid_search.best_estimator_,
    "outputs/lapse_model.joblib"
)

print("\nSelected model saved successfully!")

# Reload the saved model
loaded_model = joblib.load("outputs/lapse_model.joblib")

# Verify predictions are identical
original_predictions = grid_search.best_estimator_.predict(X_test)
loaded_predictions = loaded_model.predict(X_test)

print(
    "Predictions identical after reload:",
    (original_predictions == loaded_predictions).all()
)