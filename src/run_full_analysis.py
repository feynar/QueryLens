import json
import os
import sys

from src.analysis.static_analyzer import analyze_sql
from src.analysis.prototype_plan_analyzer import parse_plan
from src.correlation.correlator import correlate
from src.metrics.evaluation_metrics import generate_metrics
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]  # from src/scripts → project root
ARTIFACTS = PROJECT_ROOT / "artifacts"

def save_json(data, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=4)

def main_batch(plans_folder):
    print("\n=== Running QueryLens Batch Analysis ===")

    all_static = []
    all_runtime = []
    all_correlated = []

    for file in os.listdir(plans_folder):
        if file.endswith(".sql"):
            base = file.replace(".sql", "")
            sql_file = os.path.join(plans_folder, base + ".sql")
            plan_file = os.path.join(plans_folder, base + ".sqlplan")

            print(f"Processing {base}...")

            static_results = analyze_sql(sql_file)
            runtime_results = parse_plan(plan_file)
            correlation_results = correlate(static_results, runtime_results)

            all_static.extend(static_results)
            all_runtime.extend(runtime_results)
            all_correlated.extend(correlation_results)

    save_json(all_static, ARTIFACTS / "analyzer/static_results.json")
    save_json(all_runtime, ARTIFACTS / "analyzer/plan_results.json")
    save_json(all_correlated, ARTIFACTS / "reports/correlation_output.json")

    generate_metrics(
        ARTIFACTS / "reports/correlation_output.json",
        ARTIFACTS / "eval/evaluation_metrics.json"
    )

    print("✔ Batch analysis complete")
    print("✔ Evaluation metrics generated")


if __name__ == "__main__":
    main_batch("plans")