
from pathlib import Path

import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.linear_model import LogisticRegression


# ==================================================
# ASD-SCOPE: FEATURE SET COMPARISON
# ==================================================

ROOT = Path(__file__).resolve().parent.parent

DATA_PATH = ROOT / "data" / "processed" / "asd_screening_prepared.csv"
REPORT_DIR = ROOT / "outputs" / "reports"

REPORT_DIR.mkdir(parents=True, exist_ok=True)

TARGET = "Class/ASD"
QUESTIONNAIRE_COLS = [f"A{i}_Score" for i in range(1, 11)]
EXCLUDED_COLS = [TARGET, "result", "austim"]

df = pd.read_csv(DATA_PATH)
df[TARGET] = df[TARGET].astype(str).str.strip().str.upper()
df = df[df[TARGET].isin(["YES", "NO"])].copy()

y = df[TARGET]

# Model A: all eligible features, including questionnaire scores.
X_full = df.drop(
    columns=[col for col in EXCLUDED_COLS if col in df.columns]
).copy()

# Model B: background features only.
# Exclude questionnaire scores, total score, and target.
X_background = X_full.drop(
    columns=[col for col in QUESTIONNAIRE_COLS if col in X_full.columns]
).copy()


def build_pipeline(X):
    """Create preprocessing and Logistic Regression pipeline."""
    numeric_cols = X.select_dtypes(include=["number"]).columns.tolist()
    categorical_cols = [
        col for col in X.columns if col not in numeric_cols
    ]

    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )

    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OneHotEncoder(handle_unknown="ignore")),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("numeric", numeric_pipeline, numeric_cols),
            ("categorical", categorical_pipeline, categorical_cols),
        ]
    )

    return Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            (
                "classifier",
                LogisticRegression(
                    max_iter=2000,
                    class_weight="balanced",
                    random_state=42,
                ),
            ),
        ]
    )


# Use the same folds for a fair comparison.
cv = StratifiedKFold(
    n_splits=5,
    shuffle=True,
    random_state=42,
)

scoring = {
    "accuracy": "accuracy",
    "precision_macro": "precision_macro",
    "recall_macro": "recall_macro",
    "f1_macro": "f1_macro",
    "roc_auc": "roc_auc",
}

experiments = [
    ("Full screening model", X_full),
    ("Background-only model", X_background),
]

rows = []

print("=" * 65)
print("ASD-SCOPE | FEATURE SET COMPARISON")
print("=" * 65)
print(f"\nDataset rows: {len(df)}")
print(f"Target counts:\n{y.value_counts().to_string()}")

for experiment_name, X in experiments:
    print("\n" + "-" * 65)
    print(experiment_name)
    print("-" * 65)
    print(f"Number of input features before encoding: {X.shape[1]}")
    print("Features:", ", ".join(X.columns))

    pipeline = build_pipeline(X)

    # n_jobs=1 avoids Windows worker-process problems.
    results = cross_validate(
        pipeline,
        X,
        y,
        cv=cv,
        scoring=scoring,
        n_jobs=1,
        error_score="raise",
    )

    row = {
        "experiment": experiment_name,
        "feature_count_before_encoding": X.shape[1],
    }

    for metric in scoring:
        values = results[f"test_{metric}"]
        row[f"{metric}_mean"] = values.mean()
        row[f"{metric}_std"] = values.std()

        print(
            f"{metric:18s}: {values.mean():.4f} "
            f"(standard deviation: {values.std():.4f})"
        )

    rows.append(row)

comparison = pd.DataFrame(rows)

output_path = REPORT_DIR / "feature_set_comparison.csv"
comparison.to_csv(output_path, index=False)

print("\n" + "=" * 65)
print("COMPARISON SUMMARY")
print("=" * 65)

print(
    comparison[
        [
            "experiment",
            "accuracy_mean",
            "precision_macro_mean",
            "recall_macro_mean",
            "f1_macro_mean",
            "roc_auc_mean",
        ]
    ].to_string(index=False, float_format=lambda value: f"{value:.4f}")
)

print(f"\nSaved comparison report to:\n{output_path}")

print(
    "\nInterpretation: this experiment compares prediction of the dataset's "
    "screening label. It does not measure clinical diagnostic accuracy."
)
