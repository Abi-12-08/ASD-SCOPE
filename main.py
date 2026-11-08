
from pathlib import Path
import subprocess
import sys


# ==================================================
# ASD-SCOPE | MASTER PROJECT RUNNER
# ==================================================

PROJECT_DIR = Path(__file__).resolve().parent

PIPELINE_STEPS = [
    ("Data preprocessing", PROJECT_DIR / "src" / "preprocessing.py"),
    ("Exploratory data analysis", PROJECT_DIR / "src" / "eda.py"),
    ("Five-model classification", PROJECT_DIR / "src" / "classification.py"),
    ("Model diagnostics", PROJECT_DIR / "src" / "diagnose_model.py"),
    ("Feature-set comparison", PROJECT_DIR / "src" / "feature_set_comparison.py"),
]


def run_step(name, script_path):
    print("\n" + "=" * 70, flush=True)
    print(f"ASD-SCOPE | {name}", flush=True)
    print("=" * 70, flush=True)

    if not script_path.exists():
        raise FileNotFoundError(
            f"Required script not found: {script_path}"
        )

    subprocess.run(
        [sys.executable, str(script_path)],
        cwd=PROJECT_DIR,
        check=True,
    )


def main():
    print("=" * 70)
    print("ASD-SCOPE | COMPLETE PROJECT PIPELINE")
    print("=" * 70)
    print(f"Project directory: {PROJECT_DIR}")
    print(f"Python interpreter: {sys.executable}")

    try:
        for name, script_path in PIPELINE_STEPS:
            run_step(name, script_path)

    except (FileNotFoundError, subprocess.CalledProcessError) as error:
        print("\n" + "!" * 70)
        print("PIPELINE STOPPED")
        print(str(error))
        print("Fix the reported issue before continuing.")
        print("!" * 70)
        sys.exit(1)

    print("\n" + "=" * 70)
    print("ASD-SCOPE | ALL PIPELINE STEPS COMPLETED")
    print("=" * 70)
    print("Check the outputs/figures and outputs/reports folders.")
    print(
        "Reminder: results measure prediction of the dataset's "
        "screening labels, not clinical diagnostic accuracy."
    )


if __name__ == "__main__":
    main()
