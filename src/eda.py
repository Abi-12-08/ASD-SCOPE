
from pathlib import Path

import arff
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


# --------------------------------------------------
# 1. PATHS AND CONFIGURATION
# --------------------------------------------------
PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data" / "raw"
OUTPUT_DIR = PROJECT_DIR / "outputs"
FIGURE_DIR = OUTPUT_DIR / "figures"
REPORT_DIR = OUTPUT_DIR / "reports"

FIGURE_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)

arff_files = list(DATA_DIR.glob("*.arff"))

if len(arff_files) != 1:
    raise FileNotFoundError(
        f"Expected exactly one ARFF file in {DATA_DIR}; "
        f"found {len(arff_files)}."
    )


# --------------------------------------------------
# 2. LOAD DATASET
# --------------------------------------------------
with open(arff_files[0], "r", encoding="utf-8-sig") as file:
    dataset = arff.load(file)

df = pd.DataFrame(
    dataset["data"],
    columns=[attribute[0] for attribute in dataset["attributes"]],
)

for column in df.select_dtypes(include=["object", "str"]).columns:
    df[column] = df[column].map(
        lambda value: value.strip()
        if isinstance(value, str)
        else value
    )

df = df.replace(["?", ""], pd.NA)

print("=" * 60)
print("ASD-SCOPE | DATA VALIDATION AND EDA")
print("=" * 60)
print(f"\nDataset: {arff_files[0].name}")
print(f"Original dimensions: {df.shape}")


# --------------------------------------------------
# 3. CONVERT NUMERIC FEATURES
# --------------------------------------------------
score_columns = [f"A{i}_Score" for i in range(1, 11)]

for column in score_columns + ["age", "result"]:
    df[column] = pd.to_numeric(df[column], errors="coerce")

df["Class/ASD"] = (
    df["Class/ASD"].astype("string").str.strip().str.upper()
)


# --------------------------------------------------
# 4. MISSING VALUES
# --------------------------------------------------
missing = df.isna().sum().sort_values(ascending=False)
missing = missing[missing > 0]

print("\n--- MISSING VALUES ---")
print(missing.to_string() if not missing.empty else "None")
print(f"\nTotal missing cells: {df.isna().sum().sum()}")

missing.to_csv(REPORT_DIR / "missing_values_eda.csv", header=["count"])


# --------------------------------------------------
# 5. DUPLICATE INSPECTION
# --------------------------------------------------
duplicate_count = int(df.duplicated().sum())

print("\n--- DUPLICATE INSPECTION ---")
print(f"Duplicate rows flagged: {duplicate_count}")
print("No rows will be deleted automatically.")


# --------------------------------------------------
# 6. AGE VALIDATION
# --------------------------------------------------
invalid_age = df["age"].notna() & (
    (df["age"] <= 0) | (df["age"] > 120)
)

print("\n--- AGE VALIDATION ---")
print(f"Missing ages: {df['age'].isna().sum()}")
print(f"Potentially invalid ages: {invalid_age.sum()}")

if invalid_age.any():
    print("Values requiring investigation:")
    print(df.loc[invalid_age, "age"].to_list())


# --------------------------------------------------
# 7. TARGET DISTRIBUTION
# --------------------------------------------------
print("\n--- TARGET CLASS DISTRIBUTION ---")
target_counts = df["Class/ASD"].value_counts(dropna=False)
print(target_counts.to_string())

target_counts.rename_axis("class").to_csv(
    REPORT_DIR / "target_distribution_eda.csv",
    header=["count"],
)


# --------------------------------------------------
# 8. DESCRIPTIVE STATISTICS
# --------------------------------------------------
print("\n--- NUMERICAL SUMMARY ---")
summary = df[score_columns + ["age", "result"]].describe().T
print(summary.to_string())
summary.to_csv(REPORT_DIR / "descriptive_statistics_eda.csv")


# --------------------------------------------------
# 9. SAVE INSPECTED DATASET
# --------------------------------------------------
processed_dir = PROJECT_DIR / "data" / "processed"
processed_dir.mkdir(parents=True, exist_ok=True)

inspected_path = processed_dir / "asd_screening_inspected.csv"
df.to_csv(inspected_path, index=False)


# --------------------------------------------------
# 10. INITIAL VISUALIZATIONS
# --------------------------------------------------
sns.set_theme(style="whitegrid")

plt.figure(figsize=(7, 5))
sns.countplot(data=df, x="Class/ASD")
plt.title("ASD Screening Target Distribution")
plt.xlabel("Screening class")
plt.ylabel("Number of records")
plt.tight_layout()
plt.savefig(FIGURE_DIR / "target_distribution.png", dpi=300)
plt.close()

if not missing.empty:
    plt.figure(figsize=(9, 5))
    missing.sort_values().plot(kind="barh")
    plt.title("Missing Values by Feature")
    plt.xlabel("Number of missing cells")
    plt.ylabel("Feature")
    plt.tight_layout()
    plt.savefig(FIGURE_DIR / "missing_values.png", dpi=300)
    plt.close()

score_data = df[score_columns].melt(
    var_name="Question",
    value_name="Score",
)

plt.figure(figsize=(10, 5))
sns.countplot(data=score_data, x="Score", hue="Question")
plt.title("Questionnaire Score Distributions")
plt.xlabel("Score")
plt.ylabel("Number of responses")
plt.tight_layout()
plt.savefig(FIGURE_DIR / "questionnaire_scores.png", dpi=300)
plt.close()

numeric_data = df[score_columns + ["age", "result"]]

plt.figure(figsize=(11, 8))
sns.heatmap(
    numeric_data.corr(),
    annot=True,
    fmt=".2f",
    cmap="coolwarm",
    center=0,
)
plt.title("Correlation Heatmap of Numeric Features")
plt.tight_layout()
plt.savefig(FIGURE_DIR / "correlation_heatmap.png", dpi=300)
plt.close()


# --------------------------------------------------
# 11. COMPLETION
# --------------------------------------------------
print("\n--- FILES SAVED ---")
print(f"Inspected dataset: {inspected_path}")
print(f"Reports: {REPORT_DIR}")
print(f"Charts: {FIGURE_DIR}")
print("\nDATA VALIDATION AND INITIAL EDA COMPLETE")
