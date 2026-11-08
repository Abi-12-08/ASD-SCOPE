
from pathlib import Path

import arff
import pandas as pd

# --------------------------------------------------
# 1. PROJECT PATHS
# --------------------------------------------------
PROJECT_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_DIR / "data" / "raw"
PROCESSED_DIR = PROJECT_DIR / "data" / "processed"
REPORT_DIR = PROJECT_DIR / "outputs" / "reports"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)


def load_dataset():
    """Load the original ARFF dataset."""
    files = list(RAW_DIR.glob("*.arff"))

    if len(files) != 1:
        raise FileNotFoundError(
            f"Expected one ARFF file in {RAW_DIR}; found {len(files)}."
        )

    with open(files[0], "r", encoding="utf-8-sig") as file:
        data = arff.load(file)

    columns = [attribute[0] for attribute in data["attributes"]]
    df = pd.DataFrame(data["data"], columns=columns)

    # Normalize missing markers and whitespace
    for column in df.select_dtypes(include="object").columns:
        df[column] = df[column].map(
            lambda value: value.strip()
            if isinstance(value, str) else value
        )

    df = df.replace(["?", ""], pd.NA)

    return df


def preprocess_dataset():
    """Validate data and create a cleaned-format copy."""
    df = load_dataset()

    print("=" * 60)
    print("ASD-SCOPE | PREPROCESSING")
    print("=" * 60)
    print(f"Original dataset shape: {df.shape}")

    # --------------------------------------------------
    # 2. CONVERT NUMERIC COLUMNS
    # --------------------------------------------------
    score_columns = [f"A{i}_Score" for i in range(1, 11)]

    numeric_columns = score_columns + ["age", "result"]

    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df["Class/ASD"] = (
        df["Class/ASD"].astype("string").str.strip().str.upper()
    )

    # --------------------------------------------------
    # 3. MISSING VALUE REPORT
    # --------------------------------------------------
    missing = df.isna().sum()
    missing = missing[missing > 0].sort_values(ascending=False)

    print("\nMissing values before imputation:")
    print(missing.to_string() if not missing.empty else "None")

    missing.to_csv(REPORT_DIR / "missing_before.csv", header=["count"])

    # --------------------------------------------------
    # 4. INVESTIGATE AGE VALUES
    # --------------------------------------------------
    invalid_age = df["age"].notna() & (
        (df["age"] <= 0) | (df["age"] > 120)
    )

    print("\nPotentially invalid age values:")
    print(df.loc[invalid_age, ["age", "Class/ASD"]].to_string())

    # Mark impossible ages as missing; do not remove their rows.
    df.loc[invalid_age, "age"] = pd.NA

    # --------------------------------------------------
    # 5. DUPLICATE REPORT
    # --------------------------------------------------
    duplicates = df[df.duplicated(keep=False)].copy()

    print(f"\nRows flagged as duplicates: {df.duplicated().sum()}")
    print("Duplicate records are retained for now.")

    duplicates.to_csv(
        REPORT_DIR / "duplicate_review.csv", index=False
    )

    # --------------------------------------------------
    # 6. MISSING VALUE IMPUTATION
    # --------------------------------------------------
    # Age: median imputation
    df["age"] = df["age"].fillna(df["age"].median())

    # Categorical fields: explicit Unknown category
    for column in ["ethnicity", "relation"]:
        df[column] = df[column].fillna("Unknown")

    # Do not impute target labels.
    # Rows without a known target cannot be used for supervised training.

    # --------------------------------------------------
    # 7. VALIDATE TARGET
    # --------------------------------------------------
    valid_targets = {"YES", "NO"}
    unknown_targets = ~df["Class/ASD"].isin(valid_targets)

    print("\nTarget label counts:")
    print(df["Class/ASD"].value_counts(dropna=False).to_string())

    print(
        f"\nRows with missing or unexpected target: "
        f"{unknown_targets.sum()}"
    )

    # --------------------------------------------------
    # 8. SAVE PREPARED DATA
    # --------------------------------------------------
    output_path = PROCESSED_DIR / "asd_screening_prepared.csv"
    df.to_csv(output_path, index=False)

    print(f"\nPrepared dataset saved to:\n{output_path}")
    print(f"Prepared dataset shape: {df.shape}")
    print(f"Remaining missing cells: {df.isna().sum().sum()}")
    print("\nPREPROCESSING COMPLETE")

    return df


if __name__ == "__main__":
    preprocess_dataset()
