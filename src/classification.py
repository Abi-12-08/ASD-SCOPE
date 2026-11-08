
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    classification_report,
    confusion_matrix,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC


# ==================================================
# 1. PROJECT PATHS
# ==================================================
PROJECT_DIR = Path(__file__).resolve().parent.parent

DATA_PATH = (
    PROJECT_DIR
    / "data"
    / "processed"
    / "asd_screening_prepared.csv"
)

OUTPUT_DIR = PROJECT_DIR / "outputs"
REPORT_DIR = OUTPUT_DIR / "reports"
FIGURE_DIR = OUTPUT_DIR / "figures"

REPORT_DIR.mkdir(parents=True, exist_ok=True)
FIGURE_DIR.mkdir(parents=True, exist_ok=True)


def main():

    # ==================================================
    # 2. LOAD AND VALIDATE DATA
    # ==================================================
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Prepared dataset not found: {DATA_PATH}\n"
            "Run src/preprocessing.py first."
        )

    df = pd.read_csv(DATA_PATH)

    target_column = "Class/ASD"

    # Explicitly exclude the target and potential leakage fields.
    excluded_columns = [
        target_column,
        "result",
        "austim",
    ]

    missing_columns = [
        column for column in excluded_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Expected columns are missing: {missing_columns}"
        )

    # Remove rows without a valid target label.
    df[target_column] = (
        df[target_column]
        .astype("string")
        .str.strip()
        .str.upper()
    )

    df = df[df[target_column].isin(["YES", "NO"])].copy()

    X = df.drop(columns=excluded_columns)
    y = df[target_column].astype(str)

    # Convert questionnaire scores and age to numeric.
    score_columns = [
        f"A{i}_Score" for i in range(1, 11)
    ]

    for column in score_columns + ["age"]:
        X[column] = pd.to_numeric(
            X[column], errors="coerce"
        )

    print("=" * 60)
    print("ASD-SCOPE | CLASSIFICATION")
    print("=" * 60)

    print(f"Total records: {len(df)}")
    print(f"Features used: {X.shape[1]}")
    print(f"Input feature names: {X.columns.tolist()}")
    print(f"Excluded from inputs: {excluded_columns}")
    print(f"Target column: {target_column}")

    # ==================================================
    # 3. TRAIN / TEST SPLIT
    # ==================================================
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=42,
        stratify=y,
    )

    print(f"\nTraining records: {len(X_train)}")
    print(f"Testing records: {len(X_test)}")

    print("\nTraining target distribution:")
    print(y_train.value_counts().to_string())

    print("\nTesting target distribution:")
    print(y_test.value_counts().to_string())

    # ==================================================
    # 4. PREPROCESSING PIPELINES
    # ==================================================
    numeric_features = X.select_dtypes(
        include="number"
    ).columns.tolist()

    categorical_features = X.select_dtypes(
        exclude="number"
    ).columns.tolist()

    numeric_pipeline = Pipeline([
        (
            "imputer",
            SimpleImputer(strategy="median"),
        ),
        (
            "scaler",
            StandardScaler(),
        ),
    ])

    categorical_pipeline = Pipeline([
        (
            "imputer",
            SimpleImputer(strategy="most_frequent"),
        ),
        (
            "encoder",
            OneHotEncoder(handle_unknown="ignore"),
        ),
    ])

    preprocessor = ColumnTransformer([
        (
            "numeric",
            numeric_pipeline,
            numeric_features,
        ),
        (
            "categorical",
            categorical_pipeline,
            categorical_features,
        ),
    ])

    # ==================================================
    # 5. DEFINE CLASSIFIERS
    # ==================================================
    models = {
        "Logistic Regression": LogisticRegression(
            max_iter=2000,
            class_weight="balanced",
            random_state=42,
        ),

        "Decision Tree": DecisionTreeClassifier(
            class_weight="balanced",
            random_state=42,
        ),

        "Random Forest": RandomForestClassifier(
            n_estimators=300,
            class_weight="balanced",
            random_state=42,
        ),

        "KNN": KNeighborsClassifier(
            n_neighbors=7,
        ),

        "SVM": SVC(
            class_weight="balanced",
            probability=True,
            random_state=42,
        ),
    }

    results = []

    # ==================================================
    # 6. TRAIN AND EVALUATE
    # ==================================================
    for name, model in models.items():

        print("\n" + "-" * 60)
        print(f"TRAINING: {name}")
        print("-" * 60)

        pipeline = Pipeline([
            ("preprocessing", preprocessor),
            ("model", model),
        ])

        # Preprocessing is fitted using training data only.
        pipeline.fit(X_train, y_train)

        y_pred = pipeline.predict(X_test)

        fitted_model = pipeline.named_steps["model"]

        # Find the probability column corresponding to YES.
        yes_index = list(fitted_model.classes_).index("YES")

        y_prob = pipeline.predict_proba(X_test)[:, yes_index]

        # Metrics treat YES as the positive class.
        metrics = {
            "Model": name,
            "Accuracy": accuracy_score(
                y_test, y_pred
            ),
            "Precision": precision_score(
                y_test,
                y_pred,
                pos_label="YES",
                zero_division=0,
            ),
            "Recall": recall_score(
                y_test,
                y_pred,
                pos_label="YES",
                zero_division=0,
            ),
            "F1-Score": f1_score(
                y_test,
                y_pred,
                pos_label="YES",
                zero_division=0,
            ),
            "ROC-AUC": roc_auc_score(
                (y_test == "YES").astype(int),
                y_prob,
            ),
        }

        results.append(metrics)

        print(
            classification_report(
                y_test,
                y_pred,
                labels=["NO", "YES"],
                zero_division=0,
            )
        )

        # ----------------------------------------------
        # Confusion matrix
        # ----------------------------------------------
        matrix = confusion_matrix(
            y_test,
            y_pred,
            labels=["NO", "YES"],
        )

        safe_name = name.lower().replace(" ", "_")

        plt.figure(figsize=(6, 5))

        sns.heatmap(
            matrix,
            annot=True,
            fmt="d",
            cmap="Blues",
            xticklabels=["NO", "YES"],
            yticklabels=["NO", "YES"],
        )

        plt.title(f"{name} - Confusion Matrix")
        plt.xlabel("Predicted Label")
        plt.ylabel("Actual Label")
        plt.tight_layout()

        plt.savefig(
            FIGURE_DIR / f"{safe_name}_confusion_matrix.png",
            dpi=300,
        )

        plt.close()

    # ==================================================
    # 7. SAVE MODEL COMPARISON
    # ==================================================
    results_df = pd.DataFrame(results)

    results_df = results_df.sort_values(
        by="F1-Score",
        ascending=False,
    )

    comparison_path = REPORT_DIR / "model_comparison.csv"

    results_df.to_csv(
        comparison_path,
        index=False,
    )

    print("\n" + "=" * 75)
    print("MODEL COMPARISON")
    print("=" * 75)

    print(
        results_df.round(4).to_string(index=False)
    )

    # ==================================================
    # 8. CREATE PERFORMANCE COMPARISON CHART
    # ==================================================
    plot_df = results_df.melt(
        id_vars="Model",
        value_vars=[
            "Accuracy",
            "Precision",
            "Recall",
            "F1-Score",
            "ROC-AUC",
        ],
        var_name="Metric",
        value_name="Score",
    )

    plt.figure(figsize=(13, 7))

    sns.barplot(
        data=plot_df,
        x="Model",
        y="Score",
        hue="Metric",
    )

    plt.ylim(0, 1.05)
    plt.title(
        "ASD-SCOPE: Classifier Performance Comparison"
    )
    plt.xlabel("Machine Learning Model")
    plt.ylabel("Score")
    plt.xticks(rotation=15)
    plt.legend(
        title="Evaluation Metric",
        bbox_to_anchor=(1.02, 1),
        loc="upper left",
    )
    plt.tight_layout()

    plt.savefig(
        FIGURE_DIR / "model_comparison.png",
        dpi=300,
        bbox_inches="tight",
    )

    plt.close()

    # ==================================================
    # 9. FINAL STATUS
    # ==================================================
    print("\nFILES SAVED")
    print(f"Comparison CSV: {comparison_path}")
    print(f"Figures folder: {FIGURE_DIR}")

    print("\nCLASSIFICATION COMPLETE")
    print(
        "Note: These are baseline results from one "
        "stratified holdout split, not clinical validation."
    )


if __name__ == "__main__":
    main()
