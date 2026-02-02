import json
import os
import sys

from src.scripts.static_analyzer import analyze_sql
from src.scripts.prototype_plan_analyzer import parse_plan
from src.scripts.correlator import correlate
from evaluation_metrics import generate_metrics

def save_json(data, path):
    os.makedirs("artifacts", exist_ok=True)
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

    save_json(all_static, "artifacts/static_results.json")
    save_json(all_runtime, "artifacts/runtime_results.json")
    save_json(all_correlated, "artifacts/correlation_output.json")
    generate_metrics("artifacts/correlation_output.json", "artifacts/evaluation_metrics.json")

    print("✔ Batch analysis complete")
    print("✔ Evaluation metrics generated")


if __name__ == "__main__":
    main_batch("plans")