
from pathlib import Path

import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import (
    train_test_split,
    StratifiedKFold,
    cross_validate,
)
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix


# --------------------------------------------------
# 1. LOAD THE PREPARED DATASET
# --------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent

DATA_PATH = ROOT / "data" / "processed" / "asd_screening_prepared.csv"
REPORT_DIR = ROOT / "outputs" / "reports"

REPORT_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(DATA_PATH)

target_col = "Class/ASD"
questionnaire_cols = [f"A{i}_Score" for i in range(1, 11)]

if target_col not in df.columns:
    raise ValueError(f"Target column '{target_col}' was not found.")

missing_scores = [
    col for col in questionnaire_cols if col not in df.columns
]

if missing_scores:
    raise ValueError(f"Missing questionnaire columns: {missing_scores}")

df[target_col] = df[target_col].astype(str).str.strip().str.upper()

# Keep only valid target labels.
df = df[df[target_col].isin(["YES", "NO"])].copy()

print("=" * 65)
print("ASD-SCOPE | MODEL DIAGNOSTICS")
print("=" * 65)

print(f"\nRows: {len(df)}")
print(f"Target distribution:\n{df[target_col].value_counts()}")


# --------------------------------------------------
# 2. CHECK QUESTIONNAIRE SCORE AND TARGET OVERLAP
# --------------------------------------------------

print("\n" + "=" * 65)
print("QUESTIONNAIRE SCORE DIAGNOSTICS")
print("=" * 65)

score_data = df[questionnaire_cols].apply(
    pd.to_numeric, errors="coerce"
)

questionnaire_sum = score_data.sum(axis=1, min_count=10)

if "result" in df.columns:
    result_numeric = pd.to_numeric(
        df["result"], errors="coerce"
    )

    comparable = questionnaire_sum.notna() & result_numeric.notna()

    if comparable.any():
        matches = (
            questionnaire_sum[comparable]
            == result_numeric[comparable]
        )

        print(
            "\nRows where sum of A1-A10 equals result:",
            f"{matches.sum()} / {len(matches)}",
        )

        print(
            "Proportion matching:",
            f"{matches.mean():.2%}",
        )
    else:
        print("\nCould not compare questionnaire sum with result.")
else:
    print("\nNo 'result' column found.")

df["_questionnaire_sum"] = questionnaire_sum

print("\nTarget counts by questionnaire score sum:")
print(
    pd.crosstab(
        df["_questionnaire_sum"],
        df[target_col],
        margins=True,
    ).to_string()
)

df.drop(columns=["_questionnaire_sum"], inplace=True)


# --------------------------------------------------
# 3. PREPARE INPUT FEATURES
# --------------------------------------------------

# Exclude the target, the total score, and family-history field.
excluded_cols = [target_col, "result", "austim"]

X = df.drop(
    columns=[col for col in excluded_cols if col in df.columns]
).copy()

y = df[target_col].copy()

# Convert questionnaire scores and age to numeric where possible.
for col in questionnaire_cols:
    if col in X.columns:
        X[col] = pd.to_numeric(X[col], errors="coerce")

if "age" in X.columns:
    X["age"] = pd.to_numeric(X["age"], errors="coerce")

# Identify numeric and categorical columns.
numeric_cols = X.select_dtypes(include=["number"]).columns.tolist()
categorical_cols = [
    col for col in X.columns if col not in numeric_cols
]

print("\nFeatures used:", len(X.columns))
print("Excluded columns:", [c for c in excluded_cols if c in df.columns])
print("Numeric features:", numeric_cols)
print("Categorical features:", categorical_cols)


# --------------------------------------------------
# 4. BUILD THE MACHINE-LEARNING PIPELINE
# --------------------------------------------------

numeric_pipeline = Pipeline(
    steps=[
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ]
)

categorical_pipeline = Pipeline(
    steps=[
        ("imputer", SimpleImputer(strategy="most_frequent")),
        (
            "encoder",
            OneHotEncoder(handle_unknown="ignore"),
        ),
    ]
)

preprocessor = ColumnTransformer(
    transformers=[
        ("numeric", numeric_pipeline, numeric_cols),
        ("categorical", categorical_pipeline, categorical_cols),
    ]
)

model = Pipeline(
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


# --------------------------------------------------
# 5. HOLDOUT TEST
# --------------------------------------------------

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y,
)

model.fit(X_train, y_train)
predictions = model.predict(X_test)

print("\n" + "=" * 65)
print("HOLDOUT TEST RESULTS")
print("=" * 65)

print(
    classification_report(
        y_test,
        predictions,
        labels=["NO", "YES"],
        zero_division=0,
    )
)

print("Confusion matrix (rows=actual, columns=predicted; NO, YES):")
print(confusion_matrix(y_test, predictions, labels=["NO", "YES"]))


# --------------------------------------------------
# 6. FIVE-FOLD STRATIFIED CROSS-VALIDATION
# --------------------------------------------------

print("\n" + "=" * 65)
print("5-FOLD STRATIFIED CROSS-VALIDATION")
print("=" * 65)

cv = StratifiedKFold(
    n_splits=5,
    shuffle=True,
    random_state=42,
)

scoring = [
    "accuracy",
    "precision_macro",
    "recall_macro",
    "f1_macro",
    "roc_auc",
]

# n_jobs=1 avoids launching separate worker processes on Windows.
cv_results = cross_validate(
    model,
    X,
    y,
    cv=cv,
    scoring=scoring,
    return_train_score=True,
    n_jobs=1,
    error_score="raise",
)

summary = []

for metric in scoring:
    test_values = cv_results[f"test_{metric}"]
    train_values = cv_results[f"train_{metric}"]

    row = {
        "metric": metric,
        "test_mean": test_values.mean(),
        "test_std": test_values.std(),
        "train_mean": train_values.mean(),
    }

    summary.append(row)

    print(
        f"{metric:18s} | "
        f"Test mean: {row['test_mean']:.4f} | "
        f"Test std: {row['test_std']:.4f} | "
        f"Train mean: {row['train_mean']:.4f}"
    )

summary_df = pd.DataFrame(summary)

output_path = REPORT_DIR / "logistic_regression_cv.csv"
summary_df.to_csv(output_path, index=False)

print(f"\nCross-validation report saved to:\n{output_path}")

print("\nDiagnostic run completed.")
print(
    "Reminder: these results evaluate prediction of the dataset's "
    "screening label, not a confirmed clinical diagnosis."
)
