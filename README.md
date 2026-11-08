# ASD-SCOPE: Autism Screening Data Analysis and Prediction

## 1. Project Overview

ASD-SCOPE is a machine-learning project that explores an adult autism screening dataset using data preprocessing, exploratory data analysis (EDA), classification algorithms, cross-validation, and feature-set comparison.

The project studies patterns in questionnaire responses and background information to predict the screening labels provided in the dataset.

**Important:** This project predicts dataset screening labels. It is not a clinical diagnostic system and must not be used to diagnose autism.

## 2. Objectives

- Inspect and preprocess the adult autism screening dataset.
- Identify missing values, duplicate records, and potentially invalid data.
- Explore questionnaire scores and numerical relationships through visualizations.
- Train and compare five classification algorithms.
- Evaluate Logistic Regression using stratified cross-validation.
- Compare a full screening model against a background-only model.
- Save evaluation metrics, reports, and figures for further analysis.

## 3. Dataset

The project uses the UCI Adult Autism Screening dataset.

- **Records:** 704
- **Original columns:** 21
- **Target column:** `Class/ASD`
- **Target classes:** `YES` and `NO`

The dataset contains ten questionnaire score variables (`A1_Score` to `A10_Score`), age, demographic and background variables, a questionnaire result score, and the screening target.

The dataset includes missing values and a potentially invalid age value that are examined during preprocessing.

## 4. Technologies Used

- Python
- pandas and NumPy
- scikit-learn
- Matplotlib and Seaborn
- liac-arff
- Visual Studio Code

## 5. Project Structure

```text
ASD-SCOPE/
├── data/
│   ├── raw/
│   └── processed/
├── outputs/
│   ├── figures/
│   └── reports/
├── src/
│   ├── preprocessing.py
│   ├── eda.py
│   ├── classification.py
│   ├── diagnose_model.py
│   └── feature_set_comparison.py
├── main.py
├── requirements.txt
└── README.md
```

## 6. Methodology

### 6.1 Data Preprocessing

The preprocessing script loads the ARFF dataset, converts numeric columns, standardizes target labels, reports missing values, flags duplicate rows, and identifies potentially invalid ages.

Missing ages are imputed using the median. Missing ethnicity and relation values are assigned an `Unknown` category. The prepared dataset is saved as `data/processed/asd_screening_prepared.csv`.

### 6.2 Exploratory Data Analysis

The EDA script generates descriptive statistics and visualizations, including:

- Screening target distribution
- Missing values by feature
- Questionnaire score distributions
- Correlation heatmap

Reports and charts are saved under `outputs/reports/` and `outputs/figures/`.

### 6.3 Classification

Five machine-learning algorithms are evaluated:

1. Logistic Regression
2. Decision Tree
3. Random Forest
4. K-Nearest Neighbors (KNN)
5. Support Vector Machine (SVM)

The classification pipeline uses a stratified train-test split and preprocessing pipelines for numerical and categorical features. Evaluation includes accuracy, precision, recall, F1-score, ROC-AUC, and confusion matrices.

### 6.4 Model Diagnostics

The diagnostic script examines the relationship between questionnaire scores and the target labels. It also evaluates Logistic Regression with five-fold stratified cross-validation.

### 6.5 Feature-Set Comparison

Two feature sets are compared:

- **Full screening model:** questionnaire scores and background variables.
- **Background-only model:** demographic and background variables without questionnaire scores.

The comparison uses cross-validation metrics to examine how much predictive information is associated with the questionnaire scores.

## 7. Key Findings

The dataset contains 704 records: 515 labelled `NO` and 189 labelled `YES`.

The questionnaire-score analysis found that the sum of `A1_Score` through `A10_Score` equals the `result` value for every record. In this dataset, scores from 0 to 6 correspond to `NO`, while scores from 7 to 10 correspond to `YES`.

The full screening model achieved a mean cross-validation accuracy of approximately 99.57%, while the background-only model achieved approximately 67.61%.

These results show that questionnaire responses strongly reproduce the screening labels in this dataset. They do not establish that the model can independently identify clinical autism diagnoses.

## 8. Output Files

### Figures

The `outputs/figures/` directory contains the EDA charts, model comparison chart, and confusion matrices for the five classifiers.

### Reports

The `outputs/reports/` directory contains descriptive statistics, missing-value reports, duplicate review information, target distribution, classification metrics, cross-validation results, and feature-set comparison results.

## 9. Installation and Execution

### Requirements

Python 3.12 or a compatible Python environment is recommended.

Install the required packages:

```bash
python -m pip install -r requirements.txt
```

Ensure the original ARFF dataset is present in `data/raw/`.

Run the complete workflow from the project root:

```bash
python main.py
```

The master runner executes preprocessing, EDA, classification, model diagnostics, and feature-set comparison in sequence. If a step fails, resolve the reported error before relying on the generated outputs.

## 10. Limitations

- The project uses a single screening dataset containing 704 records.
- The screening labels are strongly determined by the questionnaire-score total.
- Near-perfect model performance may reflect reproduction of the dataset's label-generation rule rather than independent clinical prediction.
- The results have not established generalization to an independent population or clinical setting.
- Duplicate records are flagged and retained rather than automatically removed.
- Model performance should be interpreted as screening-label prediction, not clinical diagnostic accuracy.

## 11. Conclusion

ASD-SCOPE demonstrates a complete machine-learning workflow for adult autism screening data, from preprocessing and EDA through model evaluation and feature-set comparison. The project highlights the predictive value of questionnaire responses while demonstrating why label construction, data quality, and appropriate interpretation are essential when evaluating machine-learning results.

## 12. Data Source

UCI Machine Learning Repository — Adult Autism Screening Data:

https://archive.ics.uci.edu/dataset/426/autism
