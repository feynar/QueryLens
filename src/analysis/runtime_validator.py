"""
QueryLens — Runtime Validation Evaluator (Week 10)

Evaluates whether detected SQL anti-patterns
are confirmed by execution plan evidence.

Dataset:
Runtime workload = plans/
"""

import os
import json

from src.analysis.static_analyzer import analyze_sql
from src.analysis.prototype_plan_analyzer import parse_plan
from src.correlation.correlator import correlate


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

RUNTIME_WORKLOAD_DIR = os.path.join(PROJECT_ROOT, "plans")

OUTPUT_PATH = os.path.join(PROJECT_ROOT, "artifacts", "eval", "full_pipeline_report.json")


# -------------------------------------------------
# Find matching .sqlplan file
# -------------------------------------------------
def find_plan_file(sql_path):
    base = os.path.splitext(sql_path)[0]
    plan_path = base + ".sqlplan"

    if os.path.exists(plan_path):
        return plan_path

    return None


# -------------------------------------------------
# Evaluate one query
# -------------------------------------------------
def evaluate_query(sql_path):
    sql_name = os.path.basename(sql_path)

    # 1️⃣ Static analysis
    static_findings = analyze_sql(sql_path)

    # 2️⃣ Runtime analysis
    plan_path = find_plan_file(sql_path)

    runtime_findings = []
    if plan_path:
        runtime_findings = parse_plan(plan_path)

    # 3️⃣ Correlation
    correlations = correlate(static_findings, runtime_findings)
    confirmed = [c for c in correlations if c["confirmed"]]

    static_count = len(static_findings)
    confirmed_count = len(confirmed)

    rate = confirmed_count / static_count if static_count else 0

    return {
        "query": sql_name,
        "static_warnings": static_count,
        "confirmed_warnings": confirmed_count,
        "confirmation_rate": round(rate, 3)
    }


# -------------------------------------------------
# Compute global metrics
# -------------------------------------------------
def compute_global_metrics(rows):
    total_static = sum(r["static_warnings"] for r in rows)
    total_confirmed = sum(r["confirmed_warnings"] for r in rows)

    rate = total_confirmed / total_static if total_static else 0

    return {
        "total_static_warnings": total_static,
        "total_confirmed_warnings": total_confirmed,
        "confirmation_rate": round(rate, 3)
    }


# -------------------------------------------------
# Main pipeline
# -------------------------------------------------
def run_full_evaluation():
    results = []

    for file in os.listdir(RUNTIME_WORKLOAD_DIR):
        if file.endswith(".sql"):
            sql_path = os.path.join(RUNTIME_WORKLOAD_DIR, file)
            results.append(evaluate_query(sql_path))

    metrics = compute_global_metrics(results)

    report = {
        "per_query_results": results,
        "global_metrics": metrics
    }

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    with open(OUTPUT_PATH, "w") as f:
        json.dump(report, f, indent=4)

    print("✔ Runtime Validation evaluation complete")
    print(json.dumps(metrics, indent=4))


if __name__ == "__main__":
    run_full_evaluation()